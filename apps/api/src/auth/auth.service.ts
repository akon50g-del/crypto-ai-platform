import { ConflictException, Injectable, UnauthorizedException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import * as bcrypt from 'bcryptjs';
import { PrismaService } from '../prisma/prisma.service';
import { LoginDto, RegisterDto } from './dto';

@Injectable()
export class AuthService {
  constructor(private prisma: PrismaService, private jwt: JwtService) {}

  async issueToken(user: { id: string; email: string; planTier: string }) {
    const payload = { sub: user.id, email: user.email, plan: user.planTier };
    return { access_token: await this.jwt.signAsync(payload), user: this.publicUser(user) };
  }

  publicUser(user: any) {
    const { passwordHash, ...rest } = user;
    return rest;
  }

  async register(dto: RegisterDto) {
    const exists = await this.prisma.user.findUnique({ where: { email: dto.email } });
    if (exists) throw new ConflictException('email already registered');
    const passwordHash = await bcrypt.hash(dto.password, 12);
    const user = await this.prisma.user.create({
      data: {
        email: dto.email, passwordHash, name: dto.name ?? null,
        subscription: { create: { planTier: 'FREE', status: 'ACTIVE' } },
        preferences: { create: { strategies: ["A", "B", "C", "D"] } },
      },
    });
    return this.issueToken(user);
  }

  async login(dto: LoginDto) {
    const user = await this.prisma.user.findUnique({ where: { email: dto.email } });
    if (!user || !user.passwordHash) throw new UnauthorizedException('invalid credentials');
    const ok = await bcrypt.compare(dto.password, user.passwordHash);
    if (!ok) throw new UnauthorizedException('invalid credentials');
    return this.issueToken(user);
  }

  async findOrCreateGoogleUser(profile: { googleId: string; email: string; name?: string; avatarUrl?: string }) {
    let user = await this.prisma.user.findFirst({
      where: { OR: [{ googleId: profile.googleId }, { email: profile.email }] },
    });
    if (!user) {
      user = await this.prisma.user.create({
        data: {
          email: profile.email, googleId: profile.googleId, name: profile.name ?? null,
          avatarUrl: profile.avatarUrl ?? null, emailVerified: new Date(),
          subscription: { create: { planTier: 'FREE', status: 'ACTIVE' } },
          preferences: { create: { strategies: ["A", "B", "C", "D"] } },
        },
      });
    } else if (!user.googleId) {
      user = await this.prisma.user.update({
        where: { id: user.id }, data: { googleId: profile.googleId },
      });
    }
    return user;
  }

  async me(userId: string) {
    const user = await this.prisma.user.findUnique({
      where: { id: userId },
      include: { subscription: true, preferences: true, watchlist: true },
    });
    if (!user) throw new UnauthorizedException();
    return this.publicUser(user);
  }
}
