export interface AuthUser {
  uid: string;
  email: string | null;
  displayName: string | null;
}

export interface UserResponse {
  id: number;
  firebase_uid: string;
  email: string;
  display_name: string | null;
}
