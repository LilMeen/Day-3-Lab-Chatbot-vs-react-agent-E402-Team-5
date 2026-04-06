import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { ChatModule } from './module/chat/chat.module';
import { InfoModule } from './module/info/info.module';

@Module({
  imports: [ChatModule, InfoModule],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
