import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { Router, RouterLink, RouterOutlet } from '@angular/router';
import { ButtonModule } from 'primeng/button';
import { AuthService } from '../core/auth/auth.service';

@Component({
  selector: 'app-shell',
  imports: [RouterOutlet, RouterLink, ButtonModule],
  template: `
    <div class="app-shell app-dark">
      <aside class="sidebar" [class.sidebar-open]="menuOpen()">
        <a routerLink="/" class="brand text-decoration-none">
          <span class="brand-mark">FI</span>
          <span><strong>Forex</strong><small>Intelligence</small></span>
        </a>
        <nav class="nav flex-column mt-4">
          <a routerLink="/" class="nav-link active"><i class="pi pi-chart-line"></i><span>Overview</span></a>
          <span class="nav-link disabled"><i class="pi pi-database"></i><span>Market Data</span></span>
          <span class="nav-link disabled"><i class="pi pi-sparkles"></i><span>AI Intelligence</span></span>
        </nav>
        <div class="sidebar-footer">
          <button pButton severity="secondary" [text]="true" (click)="logout()">
            <i class="pi pi-sign-out"></i><span pButtonLabel>Sign out</span>
          </button>
        </div>
      </aside>
      <main class="content-wrap">
        <header class="topbar">
          <button class="menu-toggle" type="button" (click)="menuOpen.set(!menuOpen())" aria-label="Toggle navigation">
            <i class="pi pi-bars"></i>
          </button>
          <div>
            <div class="topbar-title">Operations Dashboard</div>
            <div class="topbar-subtitle">WIB display • canonical market data remains UTC</div>
          </div>
        </header>
        <section class="page-content"><router-outlet /></section>
      </main>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class AppShellComponent {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  readonly menuOpen = signal(false);

  logout(): void {
    this.auth.logout();
    void this.router.navigate(['/login']);
  }
}
