import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth';
import { TransferService } from '../../services/transfer';

@Component({
  selector: 'app-interior-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './interior-dashboard.html',
  styleUrl: './interior-dashboard.css'
})
export class InteriorDashboardComponent {
  private authService = inject(AuthService);
  private transferService = inject(TransferService);

  selectedFile: File | null = null;
  recipient = '';
  statusMessage = '';

  onFileSelected(event: any): void {
    if (event.target.files.length > 0) {
      this.selectedFile = event.target.files[0];
    }
  }

  onUpload(): void {
    if (!this.selectedFile || !this.recipient) {
      this.statusMessage = 'Please select a file and specify a recipient.';
      return;
    }

    this.transferService.uploadFile(this.selectedFile, this.recipient).subscribe({
      next: (res) => {
        this.statusMessage = 'File encrypted and uploaded successfully!';
        this.selectedFile = null;
        this.recipient = '';
      },
      error: (err) => {
        this.statusMessage = 'Upload failed. Please check backend connection.';
      }
    });
  }

  logout(): void {
    this.authService.logout();
  }
}