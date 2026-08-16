import { Component, OnDestroy, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { Subscription, interval, switchMap } from 'rxjs';
import { Mission } from 'src/app/services/models/mission';
import { MissionService } from 'src/app/services/mission.service';
import { AuthService } from 'src/app/services/auth.service';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit, OnDestroy {
  missions: Mission[] = [];
  private pollingSubscription?: Subscription;

  constructor(
    private missionService: MissionService,
    private authService: AuthService,
    private router: Router
  ) { }

  ngOnInit(): void {
    if (!this.authService.isAuthenticated()) {
      this.router.navigate(['/login']);
      return;
    }
    this.startPolling();
  }

  ngOnDestroy(): void {
    this.pollingSubscription?.unsubscribe();
  }

  logout(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }

  onMissionCreated(): void {
    this.missionService.list().subscribe({
      next: (missions) => this.missions = missions
    });
  }

  get missionCount(): number {
    return this.missions.length;
  }

  private startPolling(): void {
    this.missionService.list().subscribe({
      next: (missions) => this.missions = missions,
      error: () => { }
    });


    this.pollingSubscription = interval(1000).pipe(
      switchMap(() => this.missionService.list())
    ).subscribe({
      next: (missions) => this.missions = missions,
      error: () => { }
    });
  }
}