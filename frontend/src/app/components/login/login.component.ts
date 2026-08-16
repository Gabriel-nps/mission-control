import { Component } from "@angular/core";
import { Router } from "@angular/router";
import { finalize } from "rxjs";
import { AuthService } from "src/app/services/auth.service";

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent {
  username = '';
  password = '';
  errorMessage = '';
  loading = false;


  constructor(private authService: AuthService, private router: Router) { }

  get isFormValid(): boolean {
    return this.username.length > 0 && this.password.length > 0;
  }

  login(): void {
    this.loading = true;
    this.errorMessage = '';

    this.authService.login(this.username, this.password).pipe(
      finalize(() => this.loading = false)
    ).subscribe({
      next: () => this.router.navigate(['/dashboard']),
      error: (err) => {
        this.errorMessage = err.status === 401 ? 'Authentication failed' : 'Service unavailable';
      }
    });
  }
}