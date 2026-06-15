import { API_BASE_URL } from './config';

const uploadImage = (imageFile, category, userId = 'default_user') => {
  const formData = new FormData();
  formData.append('image', imageFile);

  const encodedUserId = encodeURIComponent(userId);

  return fetch(`${API_BASE_URL}/upload-image/${category}?user_id=${encodedUserId}`, {
    method: 'POST',
    body: formData,
  }).then(async (response) => {
    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      throw new Error(errorBody.error || 'Network response was not ok.');
    }

    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('image/')) {
      const blob = await response.blob();
      return {
        status: 'complete',
        imageUrl: URL.createObjectURL(blob),
      };
    }

    return response.json();
  });
};

export default uploadImage;
