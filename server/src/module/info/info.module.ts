import { Module } from '@nestjs/common';
import { InfoController } from './info.controller';
import { InfoRepository } from './info.repository';
import { InfoService } from './info.service';

@Module({
  controllers: [InfoController],
  providers: [InfoService, InfoRepository],
  exports: [InfoService],
})
export class InfoModule {}
