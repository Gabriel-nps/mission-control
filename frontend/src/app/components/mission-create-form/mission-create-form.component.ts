import { Component, EventEmitter, Output } from "@angular/core";
import { MissionService } from "src/app/services/mission.service";

@Component({
  selector: 'app-mission-create-form',
  templateUrl: './mission-create-form.component.html',
  styleUrls: ['./mission-create-form.component.scss']
})
export class MissionCreateFormComponent {
  @Output() missionCreated = new EventEmitter<void>();

  name = '';
  priority = 'LOW';
  errorMessage = '';
  loading = false;

  priorities = ['LOW', 'MEDIUM', 'HIGH'];

  constructor(private missionService: MissionService) { }

  get isFormValid(): boolean {
    return this.name.length >= 2 && this.name.length <= 128;
  }

  submit(): void {
    this.loading = true;
    this.errorMessage = '';

    this.missionService.create(this.name, this.priority).subscribe({
      next: () => {
        this.name = '',
          this.priority = 'LOW';
        this.loading = false;
        this.missionCreated.emit();
      },
      error: (err) => {
        this.loading = false;
        this.errorMessage = err.error?.detail || 'Failed to create mission';
      }
    });
  }
}