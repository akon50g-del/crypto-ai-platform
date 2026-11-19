import { Injectable } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { PassportStrategy } from '@nestjs/passport';
import { Strategy, VerifyCallback } from 'passport-google-oauth20';
import { AuthService } from './auth.service';

// Registered only when GOOGLE_CLIENT_ID/SECRET are set (see auth.module.ts).
@Injectable()
export class GoogleStrategy extends PassportStrategy(Strategy, 'google') {
  constructor(config: ConfigService, private auth: AuthService) {
    super({
      clientID: config.get<string>('GOOGLE_CLIENT_ID', 'disabled'),
      clientSecret: config.get<string>('GOOGLE_CLIENT_SECRET', 'disabled'),
      callbackURL: config.get<string>('GOOGLE_CALLBACK_URL', 'http://localhost:4000/auth/google/callback'),
      scope: ['email', 'profile'],
    });
  }
  async validate(_at: string, _rt: string, profile: any, done: VerifyCallback) {
    const user = await this.auth.findOrCreateGoogleUser({
      googleId: profile.id,
      email: profile.emails?.[0]?.value,
      name: profile.displayName,
      avatarUrl: profile.photos?.[0]?.value,
    });
    done(null, user);
  }
}
