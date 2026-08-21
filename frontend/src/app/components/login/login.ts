import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.html',
  styleUrl: './login.css'
})
export class LoginComponent {
  private authService = inject(AuthService);
  private router = inject(Router);

  username = '';
  password = '';
  errorMessage = '';

  onLogin(): void {
  this.authService.login(this.username, this.password).subscribe({
    next: () => {
      const role = this.authService.getRole();
      if (role === 'CNI') {
        this.router.navigate(['/cni']);
      } else if (role === 'MINISTRY_OF_INTERIOR') {
        this.router.navigate(['/interior']);
      } else {
        this.errorMessage = 'Unknown role — contact admin.';
      }
    },
    error: (err) => {
      this.errorMessage = 'Invalid username or password';
    }
  });
}
}