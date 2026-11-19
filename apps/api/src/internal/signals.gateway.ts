import { WebSocketGateway, WebSocketServer } from '@nestjs/websockets';
import { Server } from 'socket.io';

/** Live signal stream: clients connect to /ws/signals and receive
 *  `signal.ready` events when a new READY signal is created. */
@WebSocketGateway({ path: '/ws/signals', cors: { origin: true } })
export class SignalsGateway {
  @WebSocketServer() server: Server;

  broadcastSignal(signal: any) {
    this.server?.emit('signal.ready', {
      id: signal.id, symbol: signal.symbol?.symbol, strategy: signal.strategy,
      side: signal.side, score: signal.score, grade: signal.grade,
      entry_zone: [signal.entryZoneLow, signal.entryZoneHigh],
      stop_loss: signal.stopLoss, tp1: signal.tp1, tp2: signal.tp2,
      reason_ar: signal.reasonAr, created_at: signal.createdAt,
    });
  }
}
