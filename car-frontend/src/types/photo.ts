export type OperationType = 'car_segmentation' | 'car_part_segmentation' | 'edit_photo';
export type PhotoStatus = 'preview' | 'generating' | 'completed';

export interface PhotoResponse {
  id: number;
  user_id: number;
  original_filename: string;
  operation_type: OperationType;
  status: PhotoStatus;
  operation_params: Record<string, unknown> | null;
  created_at: string;
}

export interface PhotoListResponse {
  photos: PhotoResponse[];
  total: number;
}

