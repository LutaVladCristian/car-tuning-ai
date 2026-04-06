export type OperationType = 'car_segmentation' | 'car_part_segmentation' | 'edit_photo';

export interface PhotoResponse {
  id: number;
  user_id: number;
  original_filename: string;
  operation_type: OperationType;
  operation_params: Record<string, unknown> | null;
  created_at: string;
}

export interface PhotoListResponse {
  photos: PhotoResponse[];
  total: number;
}

export interface EditPhotoResponse {
  message: string;
}
