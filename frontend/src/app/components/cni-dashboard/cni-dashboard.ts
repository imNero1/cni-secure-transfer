import { Component, OnInit, inject, ChangeDetectorRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../services/auth';
import { TransferService, AuditLog } from '../../services/transfer';

@Component({
  selector: 'app-cni-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './cni-dashboard.html',
  styleUrl: './cni-dashboard.css'
})
export class CniDashboardComponent implements OnInit {
  private authService = inject(AuthService);
  private transferService = inject(TransferService);
  private cdr = inject(ChangeDetectorRef);

  logs: AuditLog[] = [];
  statusMessage = '';

  ngOnInit(): void {
    this.loadLogs();
  }

  loadLogs(): void {
    this.transferService.getAuditLogs().subscribe({
      next: (data) => {
        this.logs = data;
        this.cdr.detectChanges();
      },
      error: (err) => console.error('Failed to load audit logs', err)
    });
  }

  download(filename: string): void {
    this.transferService.downloadFile(filename).subscribe({
      next: (blob: Blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `decrypted_${filename}`;
        a.click();
        window.URL.revokeObjectURL(url);
      },
      error: (err) => {
        this.statusMessage = 'Download failed.';
      }
    });
  }

  logout(): void {
    this.authService.logout();
  }
}