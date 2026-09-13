import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { DatePipe, DecimalPipe } from '@angular/common';
import { forkJoin } from 'rxjs';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { TagModule } from 'primeng/tag';
import { TableModule } from 'primeng/table';
import { ProgressSpinnerModule } from 'primeng/progressspinner';
import { MarketDataSeriesStatus, MarketDataStatusSnapshot, SystemApiService, SystemStatus } from '../../core/api/system-api.service';

@Component({
  selector: 'app-dashboard',
  imports: [DatePipe, DecimalPipe, ButtonModule, CardModule, TagModule, TableModule, ProgressSpinnerModule],
  template: `
    <div class="d-flex flex-wrap align-items-end justify-content-between gap-3 mb-4">
      <div><div class="eyebrow">LIVE OPERATIONS</div><h1 class="page-title">Forex Intelligence</h1><p class="page-description mb-0">Backend health and canonical market-data freshness in one view.</p></div>
      <button pButton severity="secondary" [outlined]="true" (click)="load()" [loading]="loading()"><i class="pi pi-refresh" pButtonIcon></i><span pButtonLabel>Refresh</span></button>
    </div>

    @if (error()) { <div class="alert alert-warning border-0">Could not load one or more protected API endpoints. Confirm the API is running and sign in again if the token expired.</div> }

    <div class="row g-3 mb-4">
      <div class="col-12 col-md-6 col-xl-3"><p-card styleClass="metric-card"><div class="metric-label">API</div><div class="metric-value">{{ system()?.status ?? 'Unknown' }}</div><p-tag [severity]="system()?.status === 'healthy' ? 'success' : 'secondary'" [value]="system()?.name ?? 'Not connected'" /></p-card></div>
      <div class="col-12 col-md-6 col-xl-3"><p-card styleClass="metric-card"><div class="metric-label">Market session</div><div class="metric-value">{{ market()?.marketOpen ? 'Open' : 'Closed' }}</div><p-tag [severity]="market()?.marketOpen ? 'success' : 'secondary'" [value]="statusLabel(market()?.status)" /></p-card></div>
      <div class="col-12 col-md-6 col-xl-3"><p-card styleClass="metric-card"><div class="metric-label">Canonical series</div><div class="metric-value">{{ market()?.series?.length ?? 0 }} / 15</div><span class="metric-note">5 instruments × 3 timeframes</span></p-card></div>
      <div class="col-12 col-md-6 col-xl-3"><p-card styleClass="metric-card"><div class="metric-label">Detected gaps</div><div class="metric-value">{{ totalGaps() }}</div><span class="metric-note">Recent status window</span></p-card></div>
    </div>

    <p-card styleClass="table-card">
      <ng-template #title>Market data status</ng-template>
      <ng-template #subtitle>Times are presented in your browser timezone (WIB when the device is configured for Asia/Jakarta).</ng-template>
      @if (loading() && !market()) { <div class="d-flex justify-content-center p-5"><p-progress-spinner ariaLabel="Loading market status" /></div> }
      @else {
        <p-table [value]="market()?.series ?? []" [tableStyle]="{'min-width': '760px'}" [scrollable]="true">
          <ng-template #header><tr><th>Instrument</th><th>Timeframe</th><th>Status</th><th>Last close</th><th>Age</th><th>Gaps</th></tr></ng-template>
          <ng-template #body let-row><tr><td class="instrument">{{ row.instrument }}</td><td>{{ timeframeLabel(row.timeframe) }}</td><td><p-tag [severity]="severity(row.status)" [value]="statusLabel(row.status)" /></td><td>{{ row.lastCloseTime ? (row.lastCloseTime | date:'dd MMM yyyy, HH:mm:ss') : '—' }}</td><td>{{ row.ageMinutes === null ? '—' : ((row.ageMinutes | number:'1.0-1') + ' min') }}</td><td><span [class.text-warning]="row.gapCount > 0">{{ row.gapCount }}</span></td></tr></ng-template>
          <ng-template #emptymessage><tr><td colspan="6" class="text-center py-5 text-secondary">No market-data status returned yet.</td></tr></ng-template>
        </p-table>
      }
    </p-card>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class DashboardComponent {
  private readonly api = inject(SystemApiService);
  readonly system = signal<SystemStatus | null>(null);
  readonly market = signal<MarketDataStatusSnapshot | null>(null);
  readonly loading = signal(false);
  readonly error = signal(false);
  readonly totalGaps = computed(() => this.market()?.series.reduce((total, item) => total + item.gapCount, 0) ?? 0);

  constructor() { this.load(); }

  load(): void {
    this.loading.set(true);
    this.error.set(false);
    forkJoin({ system: this.api.getSystemStatus(), market: this.api.getMarketDataStatus() }).subscribe({
      next: ({ system, market }) => { this.system.set(system); this.market.set(market); this.loading.set(false); },
      error: () => { this.error.set(true); this.loading.set(false); }
    });
  }

  statusLabel(status: string | number | undefined): string {
    if (typeof status === 'string') return status;
    return ['Unknown', 'Fresh', 'Stale', 'GapDetected', 'MarketClosed'][status ?? 0] ?? 'Unknown';
  }

  timeframeLabel(value: string | number): string {
    if (typeof value === 'string') return value;
    return ({ 0: 'M15', 1: 'H1', 2: 'H4' } as Record<number, string>)[value] ?? String(value);
  }

  severity(status: string | number): 'success' | 'warn' | 'danger' | 'secondary' {
    switch (this.statusLabel(status)) {
      case 'Fresh': return 'success';
      case 'Stale':
      case 'GapDetected': return 'warn';
      case 'MarketClosed':
      case 'Unknown': return 'secondary';
      default: return 'danger';
    }
  }
}
