#property strict
#property version "0.1"
#property description "Read-only heartbeat exporter for Forex Intelligence"

input string BridgeUrl = "http://127.0.0.1:8001/v1/mt5/heartbeat";
input string SourceInstanceId = "lubuntu-mt5-primary";
input int HeartbeatIntervalSeconds = 1;

int OnInit()
  {
   if(HeartbeatIntervalSeconds < 1)
     {
      Print("HeartbeatIntervalSeconds must be at least 1.");
      return(INIT_PARAMETERS_INCORRECT);
     }

   EventSetTimer(HeartbeatIntervalSeconds);
   return(INIT_SUCCEEDED);
  }

void OnDeinit(const int reason)
  {
   EventKillTimer();
  }

void OnTimer()
  {
   string sent_at=TimeToString(TimeGMT(),TIME_DATE|TIME_SECONDS);
   string payload=StringFormat(
      "{\"schemaVersion\":\"mt5-heartbeat.v1\",\"sourceInstanceId\":\"%s\",\"sentAt\":\"%sZ\"}",
      SourceInstanceId,
      sent_at);

   char request_body[];
   int copied=StringToCharArray(payload,request_body,0,WHOLE_ARRAY,CP_UTF8);
   if(copied>0)
      ArrayResize(request_body,copied-1);

   char response_body[];
   string response_headers;
   ResetLastError();

   int status=WebRequest(
      "POST",
      BridgeUrl,
      "Content-Type: application/json\r\n",
      1000,
      request_body,
      response_body,
      response_headers);

   if(status<0)
      PrintFormat("Heartbeat failed. MQL5 error=%d",GetLastError());
   else if(status!=202)
      PrintFormat("Heartbeat rejected. HTTP status=%d",status);
  }
