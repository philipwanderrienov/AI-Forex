#property strict
#property version "0.2"
#property description "Read-only heartbeat and H1 candle exporter for Forex Intelligence"

input string HeartbeatUrl = "http://127.0.0.1:8001/v1/mt5/heartbeat";
input string EnvelopeUrl = "http://127.0.0.1:8001/v1/mt5/envelopes";
input string SourceInstanceId = "lubuntu-mt5-primary";
input string BrokerServerAlias = "demo-primary";
input string BrokerSymbol = "EURUSD";
input string CanonicalInstrument = "EURUSD";
input int HeartbeatIntervalSeconds = 1;
input int RequestTimeoutMilliseconds = 5000;

ulong Sequence = 0;
datetime LastPublishedH1OpenTime = 0;

string UtcIso(const datetime value)
  {
   MqlDateTime parts;
   if(!TimeToStruct(value,parts))
      return "";
   return StringFormat(
      "%04d-%02d-%02dT%02d:%02d:%02dZ",
      parts.year,parts.mon,parts.day,parts.hour,parts.min,parts.sec);
  }

string EscapeJson(const string value)
  {
   string escaped=value;
   StringReplace(escaped,"\\","\\\\");
   StringReplace(escaped,"\"","\\\"");
   return escaped;
  }

string NewBatchId()
  {
   const string alphabet="0123456789ABCDEFGHJKMNPQRSTVWXYZ";
   string result="";
   for(int i=0;i<26;i++)
      result+=StringSubstr(alphabet,MathRand()%32,1);
   return result;
  }

string Sha256(const string value)
  {
   uchar source[];
   uchar key[];
   uchar digest[];
   int copied=StringToCharArray(value,source,0,WHOLE_ARRAY,CP_UTF8);
   if(copied>0)
      ArrayResize(source,copied-1);
   ArrayResize(key,0);
   if(CryptEncode(CRYPT_HASH_SHA256,source,key,digest)<=0)
      return "";

   string hex="";
   for(int i=0;i<ArraySize(digest);i++)
      hex+=StringFormat("%02x",digest[i]);
   return "sha256:"+hex;
  }

int PostJson(const string url,const string payload)
  {
   char request_body[];
   int copied=StringToCharArray(payload,request_body,0,WHOLE_ARRAY,CP_UTF8);
   if(copied>0)
      ArrayResize(request_body,copied-1);

   char response_body[];
   string response_headers;
   ResetLastError();
   int status=WebRequest(
      "POST",
      url,
      "Content-Type: application/json\r\n",
      RequestTimeoutMilliseconds,
      request_body,
      response_body,
      response_headers);

   int last_error=GetLastError();
   if(status<0)
      PrintFormat("Bridge request failed. url=%s MQL5 error=%d",url,last_error);
   else if(status<200 || status>=300)
     {
      string response=CharArrayToString(response_body,0,WHOLE_ARRAY,CP_UTF8);
      PrintFormat(
         "Bridge response unexpected. url=%s status=%d MQL5 error=%d body=%s headers=%s",
         url,status,last_error,response,response_headers);
     }
   return status;
  }

void PublishHeartbeat()
  {
   string payload=StringFormat(
      "{\"schemaVersion\":\"mt5-heartbeat.v1\",\"sourceInstanceId\":\"%s\",\"sentAt\":\"%s\"}",
      EscapeJson(SourceInstanceId),
      UtcIso(TimeGMT()));

   int status=PostJson(HeartbeatUrl,payload);
   if(status>=0 && status!=202)
      PrintFormat("Heartbeat rejected. HTTP status=%d",status);
  }

bool PublishLatestFinalH1()
  {
   if(!SymbolSelect(BrokerSymbol,true))
     {
      PrintFormat("Cannot select broker symbol %s. error=%d",BrokerSymbol,GetLastError());
      return false;
     }

   MqlRates rates[];
   ArraySetAsSeries(rates,true);
   int count=CopyRates(BrokerSymbol,PERIOD_H1,1,1,rates);
   if(count!=1)
     {
      PrintFormat("CopyRates H1 failed for %s. copied=%d error=%d",BrokerSymbol,count,GetLastError());
      return false;
     }

   if(rates[0].time==LastPublishedH1OpenTime)
      return true;

   // MT5 bar times use broker/server time. For the current final candle we convert
   // using the terminal's current server-to-UTC offset. Historical DST-aware backfill
   // will be implemented separately before historical ingestion is enabled.
   int server_utc_offset=(int)(TimeTradeServer()-TimeGMT());
   datetime open_utc=rates[0].time-server_utc_offset;
   datetime close_utc=open_utc+PeriodSeconds(PERIOD_H1);
   datetime received_utc=TimeGMT();
   int digits=(int)SymbolInfoInteger(BrokerSymbol,SYMBOL_DIGITS);

   string open_price=DoubleToString(rates[0].open,digits);
   string high_price=DoubleToString(rates[0].high,digits);
   string low_price=DoubleToString(rates[0].low,digits);
   string close_price=DoubleToString(rates[0].close,digits);

   // Keep keys in lexicographic order. The Python contract hashes canonical JSON
   // with sorted keys and compact separators, so this exact record string produces
   // the same SHA-256 for this ASCII-only starter payload.
   string record=StringFormat(
      "{\"brokerServerAlias\":\"%s\",\"brokerSymbol\":\"%s\",\"close\":\"%s\",\"closeTime\":\"%s\",\"dataQuality\":\"GOOD\",\"high\":\"%s\",\"instrument\":\"%s\",\"low\":\"%s\",\"open\":\"%s\",\"openTime\":\"%s\",\"receivedAt\":\"%s\",\"schemaVersion\":\"candle.v1\",\"source\":\"MT5\",\"status\":\"FINAL\",\"tickVolume\":%I64d,\"timeframe\":\"H1\"}",
      EscapeJson(BrokerServerAlias),EscapeJson(BrokerSymbol),close_price,UtcIso(close_utc),
      high_price,EscapeJson(CanonicalInstrument),low_price,open_price,UtcIso(open_utc),
      UtcIso(received_utc),rates[0].tick_volume);

   string checksum=Sha256("["+record+"]");
   if(checksum=="")
     {
      Print("Cannot calculate candle SHA-256 checksum.");
      return false;
     }

   Sequence++;
   string envelope=StringFormat(
      "{\"schemaVersion\":\"mt5-envelope.v1\",\"batchId\":\"%s\",\"sourceInstanceId\":\"%s\",\"brokerServerAlias\":\"%s\",\"sequence\":%I64u,\"sentAt\":\"%s\",\"payloadType\":\"CANDLES\",\"records\":[%s],\"checksum\":\"%s\"}",
      NewBatchId(),EscapeJson(SourceInstanceId),EscapeJson(BrokerServerAlias),Sequence,
      UtcIso(received_utc),record,checksum);

   int status=PostJson(EnvelopeUrl,envelope);
   if(status==202)
     {
      LastPublishedH1OpenTime=rates[0].time;
      PrintFormat("Published FINAL %s H1 candle. open=%s sequence=%I64u",CanonicalInstrument,UtcIso(open_utc),Sequence);
      return true;
     }

   if(status>=0)
      PrintFormat("Candle envelope rejected. HTTP status=%d",status);
   return false;
  }

int OnInit()
  {
   if(HeartbeatIntervalSeconds<1)
     {
      Print("HeartbeatIntervalSeconds must be at least 1.");
      return INIT_PARAMETERS_INCORRECT;
     }
   if(RequestTimeoutMilliseconds<1000)
     {
      Print("RequestTimeoutMilliseconds must be at least 1000.");
      return INIT_PARAMETERS_INCORRECT;
     }
   if(CanonicalInstrument!="EURUSD")
     {
      Print("Starter milestone currently supports canonical EURUSD only.");
      return INIT_PARAMETERS_INCORRECT;
     }

   MathSrand((int)GetTickCount());
   EventSetTimer(HeartbeatIntervalSeconds);
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason)
  {
   EventKillTimer();
  }

void OnTimer()
  {
   PublishHeartbeat();
   PublishLatestFinalH1();
  }
