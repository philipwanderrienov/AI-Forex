import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface SystemStatus {
  name: string;
  status: string;
  timestamp: string;
}

export type FreshnessStatus = 'Unknown' | 'Fresh' | 'Stale' | 'GapDetected' | 'MarketClosed' | number;

export interface MarketDataSeriesStatus {
  instrument: string;
  timeframe: string | number;
  status: FreshnessStatus;
  lastOpenTime: string | null;
  lastCloseTime: string | null;
  ageMinutes: number | null;
  gapCount: number;
}

export interface MarketDataStatusSnapshot {
  status: FreshnessStatus;
  evaluatedAt: string;
  marketOpen: boolean;
  series: MarketDataSeriesStatus[];
}

@Injectable({ providedIn: 'root' })
export class SystemApiService {
  private readonly http = inject(HttpClient);

  getSystemStatus(): Observable<SystemStatus> {
    return this.http.get<SystemStatus>('/api/system-status');
  }

  getMarketDataStatus(): Observable<MarketDataStatusSnapshot> {
    return this.http.get<MarketDataStatusSnapshot>('/api/market-data/status');
  }
}
