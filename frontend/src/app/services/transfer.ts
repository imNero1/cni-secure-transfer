import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface AuditLog {
  id: number;
  filename: string;
  sender: string;
  recipient: string;
  timestamp: string;
  status: string;
}

@Injectable({
  providedIn: 'root'
})
export class TransferService {
  private http = inject(HttpClient);
  private apiUrl = 'http://localhost:8000';

  uploadFile(file: File, recipient: string): Observable<any> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('recipient', recipient);

    return this.http.post(`${this.apiUrl}/upload`, formData);
  }

  getAuditLogs(): Observable<AuditLog[]> {
    return this.http.get<AuditLog[]>(`${this.apiUrl}/logs`);
  }
}