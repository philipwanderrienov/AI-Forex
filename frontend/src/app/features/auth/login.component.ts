import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { finalize } from 'rxjs';
import { ButtonModule } from 'primeng/button';
import { CardModule } from 'primeng/card';
import { InputTextModule } from 'primeng/inputtext';
import { PasswordModule } from 'primeng/password';
import { MessageModule } from 'primeng/message';
import { AuthService } from '../../core/auth/auth.service';

@Component({
  selector: 'app-login',
  imports: [ReactiveFormsModule, ButtonModule, CardModule, InputTextModule, PasswordModule, MessageModule],
  template: `
    <main class="login-page app-dark">
      <div class="login-panel">
        <div class="login-brand mb-4"><span class="brand-mark">FI</span><div><strong>Forex Intelligence</strong><small>Decision support platform</small></div></div>
        <p-card>
          <ng-template #title>Sign in</ng-template>
          <ng-template #subtitle>Use the bootstrap API user configured on the backend.</ng-template>
          <form [formGroup]="form" (ngSubmit)="submit()" class="d-grid gap-3 mt-3">
            <label class="d-grid gap-2"><span>Username</span><input pInputText formControlName="username" autocomplete="username"></label>
            <label class="d-grid gap-2"><span>Password</span><p-password formControlName="password" [feedback]="false" [toggleMask]="true" autocomplete="current-password" /></label>
            @if (error()) { <p-message severity="error">Login failed. Check credentials and API connectivity.</p-message> }
            <button pButton type="submit" [loading]="loading()" [disabled]="form.invalid || loading()">
              <span pButtonLabel>Open dashboard</span><i class="pi pi-arrow-right" pButtonIcon></i>
            </button>
          </form>
        </p-card>
      </div>
    </main>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class LoginComponent {
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  readonly loading = signal(false);
  readonly error = signal(false);
  readonly form = this.fb.nonNullable.group({
    username: ['', Validators.required],
    password: ['', Validators.required]
  });

  submit(): void {
    if (this.form.invalid) return;
    this.loading.set(true);
    this.error.set(false);
    const { username, password } = this.form.getRawValue();
    this.auth.login(username, password).pipe(finalize(() => this.loading.set(false))).subscribe({
      next: () => void this.router.navigate(['/']),
      error: () => this.error.set(true)
    });
  }
}
