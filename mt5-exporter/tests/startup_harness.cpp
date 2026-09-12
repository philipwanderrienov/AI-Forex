// Execute production lifecycle callbacks with side-effect counters.
#include <cassert>
#include <string>
#include <iostream>
using string=std::string;
using datetime=long;
constexpr int INIT_SUCCEEDED=0, INIT_FAILED=-1, INVALID_HANDLE=-1;
constexpr int INSTRUMENT_COUNT=5, TIMEFRAME_COUNT=3;
constexpr int PERIOD_M15=15, PERIOD_H1=60, PERIOD_H4=240;
int ExpectedBrokerUtcOffsetSeconds=86401;
long VerifiedSequenceFloor=-1;
int HeartbeatIntervalSeconds=1, CandlePollIntervalSeconds=15;
int RequestTimeoutMilliseconds=5000, MaxBackfillBarsPerSeries=32;
bool ExporterReady=false, sequence_ok=true, timer_ok=true;
int SequenceGuardHandle=-1, Sequence=477;
datetime LastCandlePollAt=0;
string SourceInstanceId="test";
string BrokerSymbolEURUSD="EURUSD", BrokerSymbolGBPUSD="GBPUSD";
string BrokerSymbolEURGBP="EURGBP", BrokerSymbolEURCHF="EURCHF", BrokerSymbolXAUUSD="XAUUSD";
string BrokerSymbols[5], CanonicalInstruments[5], ExportTimeframeNames[3];
int ExportTimeframes[3];
int loads=0, timers=0, heartbeats=0, polls=0;
string chart_comment;
void Print(const string&) {}
template<class... T> void PrintFormat(const char*,T...) {}
void Comment(const string& value) { chart_comment=value; }
int StringLen(const string& value) { return value.size(); }
bool LoadCheckpoint(int,int) { ++loads; return true; }
bool LoadSequence() { ++loads; return sequence_ok; }
void MathSrand(int) {}
int GetTickCount() { return 0; }
bool EventSetTimer(int) { ++timers; return timer_ok; }
void EventKillTimer() {}
void FileClose(int) {}
void PublishHeartbeat() { ++heartbeats; }
void PollLatestFinalCandles() { ++polls; }
datetime TimeLocal() { return 100; }
// EXPORTER_LIFECYCLE
int main() {
    assert(OnInit()==INIT_SUCCEEDED);
    assert(!ExporterReady && !chart_comment.empty());
    OnTimer();
    assert(loads==0 && timers==0 && heartbeats==0 && polls==0);
    OnDeinit(0);
    assert(chart_comment.empty());
    ExpectedBrokerUtcOffsetSeconds=10800;
    VerifiedSequenceFloor=-2;
    assert(OnInit()==INIT_SUCCEEDED && !ExporterReady);
    OnTimer();
    assert(loads==0 && timers==0 && heartbeats==0);
    VerifiedSequenceFloor=477;
    sequence_ok=false;
    assert(OnInit()==INIT_FAILED && !ExporterReady);
    OnTimer();
    assert(timers==0 && heartbeats==0);
    sequence_ok=true;
    timer_ok=false;
    assert(OnInit()==INIT_FAILED && !ExporterReady);
    OnTimer();
    assert(heartbeats==0);
    timer_ok=true;
    assert(OnInit()==INIT_SUCCEEDED && ExporterReady);
    OnTimer();
    assert(heartbeats==1 && polls==1);
    OnDeinit(0);
    OnTimer();
    assert(!ExporterReady && heartbeats==1 && polls==1);
    std::cout << "startup scenarios passed\n";
}
