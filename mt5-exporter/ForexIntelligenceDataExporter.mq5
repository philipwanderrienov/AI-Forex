#property strict
#property version "0.4"
#property description "Read-only multi-symbol M15/H1/H4 candle exporter for Forex Intelligence"

input string HeartbeatUrl = "http://127.0.0.1:8001/v1/mt5/heartbeat";
input string EnvelopeUrl = "http://127.0.0.1:8001/v1/mt5/envelopes";
input string SourceInstanceId = "lubuntu-mt5-primary";
input string BrokerServerAlias = "demo-primary";

// Broker symbols are configurable because some brokers append suffixes/prefixes.
// Canonical instrument names remain fixed by the bridge contract.
input string BrokerSymbolEURUSD = "EURUSD";
input string BrokerSymbolGBPUSD = "GBPUSD";
input string BrokerSymbolEURGBP = "EURGBP";
input string BrokerSymbolEURCHF = "EURCHF";
input string BrokerSymbolXAUUSD = "XAUUSD";

input int HeartbeatIntervalSeconds = 1;
input int CandlePollIntervalSeconds = 15;
input int RequestTimeoutMilliseconds = 5000;

#define INSTRUMENT_COUNT 5
#define TIMEFRAME_COUNT 3

ulong Sequence = 0;
string SequenceStorageKey = "";
datetime LastCandlePollAt = 0;
datetime LastPublishedOpenTime[INSTRUMENT_COUNT][TIMEFRAME_COUNT];
string BrokerSymbols[INSTRUMENT_COUNT];
string CanonicalInstruments[INSTRUMENT_COUNT];
ENUM_TIMEFRAMES ExportTimeframes[TIMEFRAME_COUNT];
string ExportTimeframeNames[TIMEFRAME_COUNT];

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

string BuildSequenceStorageKey()
  {
   string source_hash=Sha256(SourceInstanceId);
   if(StringLen(source_hash)<39)
      return "";

   // Terminal Global Variable names are limited to 63 characters. A digest
   // keeps the state isolated per source instance without exposing its name.
   return "ForexIntelligence.Sequence."+StringSubstr(source_hash,7,32);
  }

bool LoadSequence()
  {
   SequenceStorageKey=BuildSequenceStorageKey();
   if(SequenceStorageKey=="")
     {
      Print("Cannot calculate persistent sequence storage key.");
      return false;
     }

   if(!GlobalVariableCheck(SequenceStorageKey))
     {
      ResetLastError();
      if(GlobalVariableSet(SequenceStorageKey,0.0)==0)
        {
         PrintFormat("Cannot initialize persistent sequence. error=%d",GetLastError());
         return false;
        }
     }

   double stored_sequence=GlobalVariableGet(SequenceStorageKey);
   if(stored_sequence<0.0 || stored_sequence>9007199254740991.0)
     {
      PrintFormat("Persistent sequence is outside the supported range: %.0f",stored_sequence);
      return false;
     }

   Sequence=(ulong)stored_sequence;
   return true;
  }

bool ReserveNextSequence()
  {
   if(Sequence>=9007199254740991)
     {
      Print("Persistent sequence has reached its supported maximum.");
      return false;
     }

   ulong next_sequence=Sequence+1;
   ResetLastError();
   if(GlobalVariableSet(SequenceStorageKey,(double)next_sequence)==0)
     {
      PrintFormat("Cannot persist the next sequence. error=%d",GetLastError());
      return false;
     }

   GlobalVariablesFlush();
   Sequence=next_sequence;
   return true;
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

bool PublishLatestFinalCandle(const int instrument_index,const int timeframe_index)
  {
   string broker_symbol=BrokerSymbols[instrument_index];
   string canonical_instrument=CanonicalInstruments[instrument_index];
   ENUM_TIMEFRAMES timeframe=ExportTimeframes[timeframe_index];
   string timeframe_name=ExportTimeframeNames[timeframe_index];

   if(!SymbolSelect(broker_symbol,true))
     {
      PrintFormat("Cannot select broker symbol %s for %s. error=%d",broker_symbol,canonical_instrument,GetLastError());
      return false;
     }

   MqlRates rates[];
   ArraySetAsSeries(rates,true);
   ResetLastError();
   int count=CopyRates(broker_symbol,timeframe,1,1,rates);
   if(count!=1)
     {
      PrintFormat(
         "CopyRates failed for %s %s (broker=%s). copied=%d error=%d",
         canonical_instrument,timeframe_name,broker_symbol,count,GetLastError());
      return false;
     }

   if(rates[0].time==LastPublishedOpenTime[instrument_index][timeframe_index])
      return true;

   // MT5 bar times use broker/server time. For current final candles we convert
   // using the terminal's current server-to-UTC offset. Historical DST-aware
   // backfill remains a separate future concern.
   int server_utc_offset=(int)(TimeTradeServer()-TimeGMT());
   datetime open_utc=rates[0].time-server_utc_offset;
   datetime close_utc=open_utc+PeriodSeconds(timeframe);
   datetime received_utc=TimeGMT();

   // Do not publish a bar until its canonical close is actually in the past.
   // This protects the bridge FINAL-candle invariant during terminal/history lag.
   if(close_utc>received_utc)
      return true;

   int digits=(int)SymbolInfoInteger(broker_symbol,SYMBOL_DIGITS);
   if(digits<0)
     {
      PrintFormat("Cannot resolve digits for broker symbol %s. error=%d",broker_symbol,GetLastError());
      return false;
     }

   string open_price=DoubleToString(rates[0].open,digits);
   string high_price=DoubleToString(rates[0].high,digits);
   string low_price=DoubleToString(rates[0].low,digits);
   string close_price=DoubleToString(rates[0].close,digits);

   // Keep keys in lexicographic order. The Python contract hashes canonical JSON
   // with sorted keys and compact separators, so this exact ASCII record string
   // produces the same SHA-256 checksum.
   string record=StringFormat(
      "{\"brokerServerAlias\":\"%s\",\"brokerSymbol\":\"%s\",\"close\":\"%s\",\"closeTime\":\"%s\",\"dataQuality\":\"GOOD\",\"high\":\"%s\",\"instrument\":\"%s\",\"low\":\"%s\",\"open\":\"%s\",\"openTime\":\"%s\",\"receivedAt\":\"%s\",\"schemaVersion\":\"candle.v1\",\"source\":\"MT5\",\"status\":\"FINAL\",\"tickVolume\":%I64d,\"timeframe\":\"%s\"}",
      EscapeJson(BrokerServerAlias),EscapeJson(broker_symbol),close_price,UtcIso(close_utc),
      high_price,EscapeJson(canonical_instrument),low_price,open_price,UtcIso(open_utc),
      UtcIso(received_utc),rates[0].tick_volume,EscapeJson(timeframe_name));

   string checksum=Sha256("["+record+"]");
   if(checksum=="")
     {
      PrintFormat("Cannot calculate SHA-256 checksum for %s %s.",canonical_instrument,timeframe_name);
      return false;
     }

   // Reserve durably before sending. A failed request may leave a harmless gap,
   // but an EA or terminal restart must never reuse a ledger sequence.
   if(!ReserveNextSequence())
      return false;

   string envelope=StringFormat(
      "{\"schemaVersion\":\"mt5-envelope.v1\",\"batchId\":\"%s\",\"sourceInstanceId\":\"%s\",\"brokerServerAlias\":\"%s\",\"sequence\":%I64u,\"sentAt\":\"%s\",\"payloadType\":\"CANDLES\",\"records\":[%s],\"checksum\":\"%s\"}",
      NewBatchId(),EscapeJson(SourceInstanceId),EscapeJson(BrokerServerAlias),Sequence,
      UtcIso(received_utc),record,checksum);

   int status=PostJson(EnvelopeUrl,envelope);
   if(status==202)
     {
      LastPublishedOpenTime[instrument_index][timeframe_index]=rates[0].time;
      PrintFormat(
         "Published FINAL %s %s candle. broker=%s open=%s sequence=%I64u",
         canonical_instrument,timeframe_name,broker_symbol,UtcIso(open_utc),Sequence);
      return true;
     }

   if(status>=0)
      PrintFormat(
         "Candle envelope rejected. instrument=%s timeframe=%s HTTP status=%d",
         canonical_instrument,timeframe_name,status);
   return false;
  }

void PollLatestFinalCandles()
  {
   for(int instrument_index=0;instrument_index<INSTRUMENT_COUNT;instrument_index++)
     {
      for(int timeframe_index=0;timeframe_index<TIMEFRAME_COUNT;timeframe_index++)
         PublishLatestFinalCandle(instrument_index,timeframe_index);
     }
  }

int OnInit()
  {
   if(HeartbeatIntervalSeconds<1)
     {
      Print("HeartbeatIntervalSeconds must be at least 1.");
      return INIT_PARAMETERS_INCORRECT;
     }
   if(CandlePollIntervalSeconds<1)
     {
      Print("CandlePollIntervalSeconds must be at least 1.");
      return INIT_PARAMETERS_INCORRECT;
     }
   if(RequestTimeoutMilliseconds<1000)
     {
      Print("RequestTimeoutMilliseconds must be at least 1000.");
      return INIT_PARAMETERS_INCORRECT;
     }

   BrokerSymbols[0]=BrokerSymbolEURUSD;
   BrokerSymbols[1]=BrokerSymbolGBPUSD;
   BrokerSymbols[2]=BrokerSymbolEURGBP;
   BrokerSymbols[3]=BrokerSymbolEURCHF;
   BrokerSymbols[4]=BrokerSymbolXAUUSD;

   CanonicalInstruments[0]="EURUSD";
   CanonicalInstruments[1]="GBPUSD";
   CanonicalInstruments[2]="EURGBP";
   CanonicalInstruments[3]="EURCHF";
   CanonicalInstruments[4]="XAUUSD";

   ExportTimeframes[0]=PERIOD_M15;
   ExportTimeframes[1]=PERIOD_H1;
   ExportTimeframes[2]=PERIOD_H4;
   ExportTimeframeNames[0]="M15";
   ExportTimeframeNames[1]="H1";
   ExportTimeframeNames[2]="H4";

   for(int instrument_index=0;instrument_index<INSTRUMENT_COUNT;instrument_index++)
     {
      if(StringLen(BrokerSymbols[instrument_index])<1)
        {
         PrintFormat("Broker symbol for %s must not be empty.",CanonicalInstruments[instrument_index]);
         return INIT_PARAMETERS_INCORRECT;
        }
      for(int timeframe_index=0;timeframe_index<TIMEFRAME_COUNT;timeframe_index++)
         LastPublishedOpenTime[instrument_index][timeframe_index]=0;
     }

   MathSrand((int)GetTickCount());
   if(!LoadSequence())
      return INIT_FAILED;

   EventSetTimer(HeartbeatIntervalSeconds);
   PrintFormat(
      "Forex Intelligence exporter initialized. instruments=%d timeframes=%d candlePollSeconds=%d nextSequence=%I64u",
      INSTRUMENT_COUNT,TIMEFRAME_COUNT,CandlePollIntervalSeconds,Sequence+1);
   return INIT_SUCCEEDED;
  }

void OnDeinit(const int reason)
  {
   EventKillTimer();
  }

void OnTimer()
  {
   PublishHeartbeat();

   datetime now=TimeLocal();
   if(LastCandlePollAt==0 || now-LastCandlePollAt>=CandlePollIntervalSeconds)
     {
      LastCandlePollAt=now;
      PollLatestFinalCandles();
     }
  }
