import { Injectable } from '@nestjs/common';
import { InfoRepository } from './info.repository';
import type { InfoRequestEntity } from './entity/info-request.entity';
import type { InfoResponseEntity } from './entity/info-response.entity';

@Injectable()
export class InfoService {
  constructor(private readonly infoRepository: InfoRepository) {}

  async getInfo(payload: InfoRequestEntity): Promise<InfoResponseEntity> {
    return this.infoRepository.getInfo(payload);
  }
}
