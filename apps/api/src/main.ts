import { ValidationPipe } from '@nestjs/common';
import { NestFactory } from '@nestjs/core';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule, { rawBody: true });
  app.enableCors({ origin: true, credentials: true });
  app.useGlobalPipes(new ValidationPipe({ whitelist: true, transform: true }));

  const config = new DocumentBuilder()
    .setTitle('Crypto AI Signals API')
    .setDescription('ICT/SMC signals platform — analysis is educational, not financial advice.')
    .setVersion('0.3.0')
    .addBearerAuth()
    .build();
  SwaggerModule.setup('docs', app, SwaggerModule.createDocument(app, config));

  const port = process.env.API_PORT ?? 4000;
  await app.listen(port);
  console.log(`API listening on http://localhost:${port} — Swagger at /docs`);
}
bootstrap();
