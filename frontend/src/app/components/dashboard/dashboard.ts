import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth';
import { TransferService, AuditLog } from '../../services/transfer';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css'
})
export class DashboardComponent implements OnInit {
  private authService = inject(AuthService);
  private transferService = inject(TransferService);

  selectedFile: File | null = null;
  recipient = '';
  statusMessage = '';
  logs: AuditLog[] = [];

  ngOnInit(): void {
    this.loadLogs();
  }

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
        this.loadLogs();
      },
      error: (err) => {
        this.statusMessage = 'Upload failed. Please check backend connection.';
      }
    });
  }

  loadLogs(): void {
    this.transferService.getAuditLogs().subscribe({
      next: (data) => {
        this.logs = data;
      },
      error: (err) => console.error('Failed to load audit logs', err)
    });
  }

  logout(): void {
    this.authService.logout();
  }
}