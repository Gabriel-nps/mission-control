import { Component,Input } from "@angular/core";
import { Mission } from "src/app/services/models/mission";

@Component({
  selector: 'app-mission-list',
  templateUrl: './mission-list.component.html',
  styleUrls: ['./mission-list.component.scss']
})
export class MissionListComponent {
  @Input() missions: Mission[] = [];
}
