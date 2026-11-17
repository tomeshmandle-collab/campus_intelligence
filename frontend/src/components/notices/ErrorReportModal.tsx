import React, { useState, useEffect } from 'react';
import {
  ErrorReportReason,
  ERROR_REPORT_REASONS,
  REASON_TO_ISSUE_TYPE,
  ErrorReportRequest,
  ErrorReportResponse,
} from '../../types/notice';
import { submitErrorReport, mockSubmitErrorReport, ApiErrorBody } from '../../services/api';

export const REPORT_REASONS: readonly ErrorReportReason[] = [
  'Incorrect Date',
  'Wrong Audience',
  'Typo in Summary',
  'Document Unreadable',
  'Other',
] as const;

export interface ErrorReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  notice?: {
    id: string;
    title: string;
    reference_number?: string | null;
  } | null;
  noticeId?: string;
  noticeTitle?: string;
  noticeReference?: string | null;
  onSuccess?: (response: ErrorReportResponse) => void;
  onSubmitReport?: (
    noticeId: string,
    payload: ErrorReportRequest
  ) => Promise<ErrorReportResponse>;
  isMockMode?: boolean;
}

export const ErrorReportModal: React.FC<ErrorReportModalProps> = ({
  isOpen,
  onClose,
  notice,
  noticeId,
  noticeTitle,
  noticeReference,
  onSuccess,
  onSubmitReport,
  isMockMode = false,
}) => {
  const targetNoticeId = notice?.id || noticeId || '';
  const targetTitle = notice?.title || noticeTitle || (targetNoticeId ? `Notice #${targetNoticeId}` : '');
  const targetRef = notice?.reference_number || noticeReference || null;

  const [reason, setReason] = useState<ErrorReportReason | ''>('');
  const [explanation, setExplanation] = useState<string>('');
  const [reporterEmail, setReporterEmail] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<{
    reason?: string;
    explanation?: string;
    email?: string;
  }>({});
  const [submitSuccess, setSubmitSuccess] = useState<boolean>(false);
  const [reportResponse, setReportResponse] = useState<ErrorReportResponse | null>(null);

  // Reset form when modal opens or closes
  useEffect(() => {
    if (isOpen) {
      setReason('');
      setExplanation('');
      setReporterEmail('');
      setApiError(null);
      setValidationErrors({});
      setSubmitSuccess(false);
      setReportResponse(null);
      setIsSubmitting(false);
    }
  }, [isOpen, targetNoticeId]);

  // Handle ESC key to close modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && !isSubmitting) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, isSubmitting, onClose]);

  if (!isOpen) {
    return null;
  }

  const validateForm = (): boolean => {
    const errors: { reason?: string; explanation?: string; email?: string } = {};

    if (!reason) {
      errors.reason = 'Please select a reason for reporting.';
    }

    const trimmedExplanation = explanation.trim();
    if (!trimmedExplanation) {
      errors.explanation = 'Please enter an explanation describing the issue.';
    } else if (trimmedExplanation.length < 10) {
      errors.explanation = `Explanation must be at least 10 characters (currently ${trimmedExplanation.length}).`;
    } else if (trimmedExplanation.length > 500) {
      errors.explanation = `Explanation cannot exceed 500 characters (currently ${trimmedExplanation.length}).`;
    }

    const trimmedEmail = reporterEmail.trim();
    if (trimmedEmail) {
      const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailPattern.test(trimmedEmail)) {
        errors.email = 'Please provide a valid email address or leave this field empty.';
      }
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setApiError(null);

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    const payload: ErrorReportRequest = {
      issue_type: reason ? REASON_TO_ISSUE_TYPE[reason] : 'other',
      description: reporterEmail.trim()
        ? `${explanation.trim()}\n\n[Contact: ${reporterEmail.trim()}]`
        : explanation.trim(),
      reporter_email: reporterEmail.trim() || undefined,
      reason: reason || undefined,
    };

    try {
      let result: ErrorReportResponse;

      if (onSubmitReport) {
        result = await onSubmitReport(targetNoticeId, payload);
      } else if (isMockMode) {
        result = await mockSubmitErrorReport(targetNoticeId, payload);
      } else {
        try {
          result = await submitErrorReport(targetNoticeId, payload);
        } catch (submitErr: unknown) {
          // If backend server is unreachable (offline dev/preview), fall back to mock
          const isNetworkError =
            (submitErr &&
              typeof submitErr === 'object' &&
              'code' in submitErr &&
              (submitErr as { code?: string }).code === 'ERR_NETWORK') ||
            (submitErr &&
              typeof submitErr === 'object' &&
              'message' in submitErr &&
              String((submitErr as { message?: string }).message).includes('Network Error'));

          if (isNetworkError) {
            result = await mockSubmitErrorReport(targetNoticeId, payload);
          } else {
            throw submitErr;
          }
        }
      }

      setReportResponse(result);
      setSubmitSuccess(true);
      onSuccess?.(result);
    } catch (err: unknown) {
      // Gracefully handle standard error envelope or Axios error
      if (err && typeof err === 'object') {
        const errorObj = err as ApiErrorBody;
        if (errorObj.message) {
          let fullMsg = errorObj.message;
          if (Array.isArray(errorObj.details) && errorObj.details.length > 0) {
            const detailStr = errorObj.details
              .map((d) => d.issue)
              .filter(Boolean)
              .join('; ');
            if (detailStr) {
              fullMsg += ` (${detailStr})`;
            }
          }
          setApiError(fullMsg);
        } else if ('message' in err && typeof (err as { message: unknown }).message === 'string') {
          setApiError(String((err as { message: string }).message));
        } else {
          setApiError('An unexpected error occurred while submitting your report. Please try again.');
        }
      } else {
        setApiError('An unexpected error occurred while submitting your report. Please try again.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      onClose();
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="report-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs transition-opacity animate-in fade-in duration-150"
      onClick={(e) => {
        if (e.target === e.currentTarget && !isSubmitting) {
          handleClose();
        }
      }}
    >
      <div className="bg-white rounded-xl shadow-2xl border border-slate-200 max-w-lg w-full overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="flex items-start justify-between p-5 border-b border-slate-100 bg-slate-50/60">
          <div className="space-y-1 pr-4">
            <h2
              id="report-modal-title"
              className="text-base sm:text-lg font-bold text-slate-900 leading-snug"
            >
              Report an Issue with this Notice
            </h2>
            <p className="text-xs text-slate-500">
              Help maintain high information accuracy by flagging factual errors, wrong categories, or unreadable scans.
            </p>
          </div>
          <button
            type="button"
            onClick={handleClose}
            disabled={isSubmitting}
            aria-label="Close dialog"
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 sm:p-6 overflow-y-auto space-y-4">
          {submitSuccess ? (
            /* Success Feedback View */
            <div className="py-4 text-center space-y-4 animate-in fade-in zoom-in-95 duration-200">
              <div className="mx-auto flex items-center justify-center h-14 w-14 rounded-full bg-emerald-100 text-emerald-600 shadow-xs">
                <svg
                  className="w-8 h-8"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth="2.5"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>

              <div className="space-y-2">
                <h3 className="text-base font-bold text-slate-900">
                  Report Received
                </h3>
                <p className="text-sm font-semibold text-emerald-800 bg-emerald-50 border border-emerald-200 rounded-lg p-3.5 leading-relaxed">
                  Thank you! Your report has been submitted to the college editorial team.
                </p>
                <p className="text-xs text-slate-500 max-w-sm mx-auto leading-relaxed pt-1">
                  Our editors will cross-reference your submission against the official circular document.
                </p>
                {reportResponse?.report_id && (
                  <div className="inline-block px-2.5 py-1 rounded bg-slate-100 text-[11px] font-mono text-slate-600">
                    Report Reference: {reportResponse.report_id}
                  </div>
                )}
              </div>

              <div className="pt-3">
                <button
                  type="button"
                  onClick={handleClose}
                  className="w-full sm:w-auto min-w-[120px] px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-xs transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                >
                  Done
                </button>
              </div>
            </div>
          ) : (
            /* Form View */
            <form onSubmit={handleSubmit} className="space-y-4" noValidate>
              {/* Notice Reference Summary */}
              {targetTitle && (
                <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-700 space-y-1">
                  <div className="flex items-center justify-between text-slate-500 text-[11px]">
                    <span className="font-semibold uppercase tracking-wider">Target Notice</span>
                    {targetRef && <span>Ref: {targetRef}</span>}
                  </div>
                  <p className="font-semibold text-slate-900 line-clamp-2">
                    {targetTitle}
                  </p>
                  {targetNoticeId && (
                    <p className="text-[11px] text-slate-400 font-mono">
                      ID: {targetNoticeId}
                    </p>
                  )}
                </div>
              )}

              {/* API Error Alert */}
              {apiError && (
                <div
                  role="alert"
                  className="rounded-lg bg-red-50 border border-red-200 p-3.5 flex items-start space-x-2.5 text-xs text-red-700"
                >
                  <svg
                    className="w-4 h-4 text-red-500 mt-0.5 shrink-0"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth="2"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                    />
                  </svg>
                  <div className="flex-1">
                    <p className="font-semibold text-red-800">Unable to submit report</p>
                    <p className="mt-0.5 leading-relaxed">{apiError}</p>
                  </div>
                </div>
              )}

              {/* Reason Selector Dropdown */}
              <div>
                <label
                  htmlFor="error-reason-select"
                  className="block text-xs font-semibold text-slate-700 mb-1"
                >
                  Issue Reason <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <select
                    id="error-reason-select"
                    value={reason}
                    onChange={(e) => {
                      setReason(e.target.value as ErrorReportReason);
                      if (validationErrors.reason) {
                        setValidationErrors((prev) => ({ ...prev, reason: undefined }));
                      }
                    }}
                    disabled={isSubmitting}
                    className={`w-full rounded-lg border px-3 py-2 text-xs sm:text-sm bg-white text-slate-900 focus:outline-none focus:ring-2 transition-colors disabled:bg-slate-50 disabled:text-slate-500 ${
                      validationErrors.reason
                        ? 'border-red-300 focus:border-red-500 focus:ring-red-200'
                        : 'border-slate-300 focus:border-indigo-500 focus:ring-indigo-200'
                    }`}
                  >
                    <option value="" disabled>
                      Select an issue reason...
                    </option>
                    {ERROR_REPORT_REASONS.map((opt) => (
                      <option key={opt} value={opt}>
                        {opt}
                      </option>
                    ))}
                  </select>
                </div>
                {validationErrors.reason && (
                  <p className="mt-1 text-xs text-red-600 font-medium">
                    {validationErrors.reason}
                  </p>
                )}
              </div>

              {/* Explanation Textarea */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label
                    htmlFor="error-explanation-textarea"
                    className="block text-xs font-semibold text-slate-700"
                  >
                    Explanation <span className="text-red-500">*</span>
                  </label>
                  <span
                    className={`text-[11px] font-mono ${
                      explanation.length === 500
                        ? 'text-amber-600 font-bold'
                        : explanation.length >= 10
                        ? 'text-slate-500'
                        : 'text-slate-400'
                    }`}
                  >
                    {explanation.length} / 500 characters
                  </span>
                </div>
                <textarea
                  id="error-explanation-textarea"
                  rows={4}
                  maxLength={500}
                  value={explanation}
                  onChange={(e) => {
                    setExplanation(e.target.value);
                    if (validationErrors.explanation) {
                      setValidationErrors((prev) => ({ ...prev, explanation: undefined }));
                    }
                  }}
                  disabled={isSubmitting}
                  placeholder="Describe the discrepancy in detail (e.g., The registration deadline in the summary says 20th Nov, but page 2 of the PDF mentions 25th Nov)..."
                  className={`w-full rounded-lg border px-3 py-2 text-xs sm:text-sm bg-white text-slate-900 focus:outline-none focus:ring-2 transition-colors resize-y disabled:bg-slate-50 disabled:text-slate-500 ${
                    validationErrors.explanation
                      ? 'border-red-300 focus:border-red-500 focus:ring-red-200'
                      : 'border-slate-300 focus:border-indigo-500 focus:ring-indigo-200'
                  }`}
                />
                <div className="flex justify-between items-center text-[11px] mt-1">
                  {validationErrors.explanation ? (
                    <span className="text-red-600 font-medium">
                      {validationErrors.explanation}
                    </span>
                  ) : explanation.length > 0 && explanation.trim().length < 10 ? (
                    <span className="text-amber-600 font-medium">
                      {10 - explanation.trim().length} more character{10 - explanation.trim().length === 1 ? '' : 's'} required (min. 10)
                    </span>
                  ) : (
                    <span className="text-slate-400">
                      Must be between 10 and 500 characters
                    </span>
                  )}
                </div>
              </div>

              {/* Optional Reporter Email */}
              <div>
                <label
                  htmlFor="reporter-email-input"
                  className="block text-xs font-semibold text-slate-700 mb-1"
                >
                  Your Email Address <span className="text-slate-400 font-normal">(Optional)</span>
                </label>
                <input
                  id="reporter-email-input"
                  type="email"
                  value={reporterEmail}
                  onChange={(e) => {
                    setReporterEmail(e.target.value);
                    if (validationErrors.email) {
                      setValidationErrors((prev) => ({ ...prev, email: undefined }));
                    }
                  }}
                  disabled={isSubmitting}
                  placeholder="e.g., rollno@kmc.du.ac.in"
                  className={`w-full rounded-lg border px-3 py-2 text-xs sm:text-sm bg-white text-slate-900 focus:outline-none focus:ring-2 transition-colors disabled:bg-slate-50 disabled:text-slate-500 ${
                    validationErrors.email
                      ? 'border-red-300 focus:border-red-500 focus:ring-red-200'
                      : 'border-slate-300 focus:border-indigo-500 focus:ring-indigo-200'
                  }`}
                />
                {validationErrors.email ? (
                  <p className="mt-1 text-xs text-red-600 font-medium">
                    {validationErrors.email}
                  </p>
                ) : (
                  <p className="mt-1 text-[11px] text-slate-400">
                    Provide your email if you wish to receive an editorial update on this correction.
                  </p>
                )}
              </div>

              {/* Form Actions */}
              <div className="flex items-center justify-end space-x-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={handleClose}
                  disabled={isSubmitting}
                  className="px-4 py-2 border border-slate-300 rounded-lg text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-400 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-lg shadow-xs text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-60 disabled:cursor-not-allowed transition-colors min-w-[120px]"
                >
                  {isSubmitting ? (
                    <>
                      <svg
                        className="animate-spin -ml-1 mr-2 h-3.5 w-3.5 text-white"
                        fill="none"
                        viewBox="0 0 24 24"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        />
                      </svg>
                      Submitting...
                    </>
                  ) : (
                    'Submit Report'
                  )}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

export default ErrorReportModal;
