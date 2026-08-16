import { Injectable } from "@angular/core";
import { HttpClient } from "@angular/common/http";
import { Observable } from "rxjs";
import { environment } from "src/environments/environment";
import { Mission } from './models/mission'

@Injectable({
  providedIn: 'root'
})
export class MissionService {
  private readonly baseUrl = `${environment.apiUrl}/missions`;

  constructor(private http: HttpClient) { }

  list(): Observable<Mission[]> {
    return this.http.get<Mission[]>(this.baseUrl);
  }

  create(name: string, priority: string): Observable<Mission> {
    return this.http.post<Mission>(this.baseUrl, { name, priority });
  }

  getById(id: string): Observable<Mission>{
    return this.http.get<Mission>(`${this.baseUrl}/${id}`);
  }
}