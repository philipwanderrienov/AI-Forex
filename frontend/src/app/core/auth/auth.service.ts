import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';

export interface TokenResponse {
  tokenType: string;
  accessToken: string;
  accessTokenExpiresAt: string;
  refreshToken: string;
  refreshTokenExpiresAt: string;
}

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly accessTokenKey = 'forex-intelligence.access-token';
  private readonly refreshTokenKey = 'forex-intelligence.refresh-token';

  login(username: string, password: string): Observable<TokenResponse> {
    return this.http.post<TokenResponse>('/api/auth/login', { username, password }).pipe(
      tap((tokens) => this.store(tokens))
    );
  }

  logout(): void {
    localStorage.removeItem(this.accessTokenKey);
    localStorage.removeItem(this.refreshTokenKey);
  }

  get accessToken(): string | null {
    return localStorage.getItem(this.accessTokenKey);
  }

  get isAuthenticated(): boolean {
    return !!this.accessToken;
  }

  private store(tokens: TokenResponse): void {
    localStorage.setItem(this.accessTokenKey, tokens.accessToken);
    localStorage.setItem(this.refreshTokenKey, tokens.refreshToken);
  }
}
