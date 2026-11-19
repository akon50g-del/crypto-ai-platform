import nodemailer from 'nodemailer';
import type { SendResult } from './telegram';

/** SMTP email sender. Without SMTP_HOST it is a dry-run (recorded, not sent). */
export async function sendEmail(to: string, subject: string, text: string): Promise<SendResult> {
  const host = process.env.SMTP_HOST;
  if (!host) return { ok: false, dryRun: true, error: 'dry-run: SMTP_HOST not set' };
  try {
    const transporter = nodemailer.createTransport({
      host,
      port: Number(process.env.SMTP_PORT ?? 587),
      secure: Number(process.env.SMTP_PORT ?? 587) === 465,
      auth: process.env.SMTP_USER ? { user: process.env.SMTP_USER, pass: process.env.SMTP_PASS } : undefined,
    });
    await transporter.sendMail({
      from: process.env.SMTP_FROM ?? 'signals@example.com',
      to, subject, text,
    });
    return { ok: true };
  } catch (e: any) {
    return { ok: false, error: e.message };
  }
}
