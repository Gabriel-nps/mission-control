import { Component, Input } from '@angular/core';
import { Mission } from 'src/app/services/models/mission';

@Component({
  selector: 'app-mission-card',
  templateUrl: './mission-card.component.html',
  styleUrls: ['./mission-card.component.scss']
})
export class MissionCardComponent {
  @Input() mission!: Mission;

  get progressPercent(): number {
    switch (this.mission.status) {
      case 'CREATED': return 33;
      case 'PROCESSING': return 66;
      case 'COMPLETED': return 100;
      case 'FAILED': return this.getFailedProgress();
      default: return 0;
    }
  }

  get statusIcon(): string {
    switch (this.mission.status) {
      case 'CREATED': return '📋';
      case 'PROCESSING': return '⚙️';
      case 'COMPLETED': return '✅';
      case 'FAILED': return '❌';
      default: return '❓';
    }
  }

  private getFailedProgress(): number {
    // FAILED stops at last reached stage — assume at least CREATED
    return 33;
  }

}
