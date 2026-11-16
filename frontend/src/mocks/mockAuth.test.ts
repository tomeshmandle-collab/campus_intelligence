/**
 * CAI Campus Intelligence — Mock Authentication Tests
 * Verifies contract fixtures for Issue P4-1 (Staff Authentication)
 */

import { authenticateMock, MOCK_STAFF_ACCOUNTS } from '../mockAuth';

describe('mockAuth fixtures', () => {
  it('authenticates valid staff uploader credentials', () => {
    const result = authenticateMock('uploader@kmc.du.ac.in', 'password123');
    expect(result).not.toBeNull();
    expect(result?.user.email).toBe('uploader@kmc.du.ac.in');
    expect(result?.user.role).toBe('uploader');
    expect(result?.token).toBeDefined();
  });

  it('authenticates valid admin credentials', () => {
    const result = authenticateMock('admin@kmc.du.ac.in', 'password123');
    expect(result).not.toBeNull();
    expect(result?.user.email).toBe('admin@kmc.du.ac.in');
    expect(result?.user.role).toBe('admin');
  });

  it('normalizes email case and whitespace', () => {
    const result = authenticateMock('   UPLOADER@KMC.DU.AC.IN   ', 'password123');
    expect(result).not.toBeNull();
    expect(result?.user.email).toBe('uploader@kmc.du.ac.in');
  });

  it('rejects incorrect password', () => {
    const result = authenticateMock('uploader@kmc.du.ac.in', 'wrongpassword');
    expect(result).toBeNull();
  });

  it('rejects unknown institutional email', () => {
    const result = authenticateMock('unknown@kmc.du.ac.in', 'password123');
    expect(result).toBeNull();
  });

  it('provides all standard mock accounts with valid roles', () => {
    expect(MOCK_STAFF_ACCOUNTS.length).toBeGreaterThanOrEqual(2);
    MOCK_STAFF_ACCOUNTS.forEach((account) => {
      expect(['uploader', 'admin']).toContain(account.user.role);
      expect(account.token.length).toBeGreaterThan(0);
    });
  });
});
