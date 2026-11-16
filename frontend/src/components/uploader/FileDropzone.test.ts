/**
 * CAI Campus Intelligence — FileDropzone Unit Tests
 * Verifies client-side validation logic and size formatting for notice PDF uploads (M02 / M04).
 */

import { formatFileSize, MAX_FILE_SIZE_BYTES } from './FileDropzone';

describe('FileDropzone helpers and constraints', () => {
  it('enforces 10MB limit in bytes', () => {
    expect(MAX_FILE_SIZE_BYTES).toBe(10 * 1024 * 1024);
  });

  it('formats file sizes accurately into KB and MB', () => {
    expect(formatFileSize(0)).toBe('0 KB');
    expect(formatFileSize(512 * 1024)).toBe('512.0 KB');
    expect(formatFileSize(1024 * 1024)).toBe('1.00 MB');
    expect(formatFileSize(2.5 * 1024 * 1024)).toBe('2.50 MB');
    expect(formatFileSize(10 * 1024 * 1024)).toBe('10.00 MB');
  });
});
