import { ApiProperty } from '@nestjs/swagger';
import { IsEmail, IsOptional, IsString, MinLength } from 'class-validator';

export class RegisterDto {
  @ApiProperty({ example: 'user@example.com' }) @IsEmail() email: string;
  @ApiProperty({ example: 'strong-password-123' }) @IsString() @MinLength(8) password: string;
  @ApiProperty({ required: false }) @IsOptional() @IsString() name?: string;
}

export class LoginDto {
  @ApiProperty({ example: 'user@example.com' }) @IsEmail() email: string;
  @ApiProperty({ example: 'strong-password-123' }) @IsString() password: string;
}
