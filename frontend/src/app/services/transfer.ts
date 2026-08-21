import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface AuditLog {
  id: number;
  filename: string;
  actor_role: string;
  action_type: string;
  has_sensitive_data: boolean;
  timestamp: string;
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

    return this.http.post(`${this.apiUrl}/api/interior/upload`, formData);
  }

  getAuditLogs(): Observable<AuditLog[]> {
    return this.http.get<AuditLog[]>(`${this.apiUrl}/api/admin/logs`);
  }

  downloadFile(filename: string): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/api/cni/download/${filename}`, {
      responseType: 'blob'
    });
  }
}