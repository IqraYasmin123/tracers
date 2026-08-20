/// Data models mirroring backend/app/schemas/*.py exactly — same field names and shapes
/// as the JSON the FastAPI backend actually returns, so there's one obvious source of
/// truth (the backend) rather than the mobile app inventing its own contract.
library;

class AnalysisResult {
  final String verdict;
  final double confidence;
  final String? attackType;
  final double? attackTypeConfidence;
  final String attributionMethod;
  final String attributionHeatmapPngBase64;
  final double attributionPeakFraction;
  final String explanationSummary;
  final List<String> explanationDetails;
  final String sha256Hash;
  final double processingTimeMs;

  AnalysisResult({
    required this.verdict,
    required this.confidence,
    this.attackType,
    this.attackTypeConfidence,
    required this.attributionMethod,
    required this.attributionHeatmapPngBase64,
    required this.attributionPeakFraction,
    required this.explanationSummary,
    required this.explanationDetails,
    required this.sha256Hash,
    required this.processingTimeMs,
  });

  factory AnalysisResult.fromJson(Map<String, dynamic> json) => AnalysisResult(
        verdict: json['verdict'] as String,
        confidence: (json['confidence'] as num).toDouble(),
        attackType: json['attack_type'] as String?,
        attackTypeConfidence: (json['attack_type_confidence'] as num?)?.toDouble(),
        attributionMethod: json['attribution_method'] as String,
        attributionHeatmapPngBase64: json['attribution_heatmap_png_base64'] as String,
        attributionPeakFraction: (json['attribution_peak_fraction'] as num).toDouble(),
        explanationSummary: json['explanation_summary'] as String,
        explanationDetails: (json['explanation_details'] as List).cast<String>(),
        sha256Hash: json['sha256_hash'] as String,
        processingTimeMs: (json['processing_time_ms'] as num).toDouble(),
      );
}

class AiResultSummary {
  final String verdict;
  final double confidence;
  final String? attackType;
  final double? attackTypeConfidence;
  final String attributionMethod;
  final String explanationSummary;
  final List<String> explanationDetails;
  final double processingTimeMs;

  AiResultSummary({
    required this.verdict,
    required this.confidence,
    this.attackType,
    this.attackTypeConfidence,
    required this.attributionMethod,
    required this.explanationSummary,
    required this.explanationDetails,
    required this.processingTimeMs,
  });

  factory AiResultSummary.fromJson(Map<String, dynamic> json) => AiResultSummary(
        verdict: json['verdict'] as String,
        confidence: (json['confidence'] as num).toDouble(),
        attackType: json['attack_type'] as String?,
        attackTypeConfidence: (json['attack_type_confidence'] as num?)?.toDouble(),
        attributionMethod: json['attribution_method'] as String,
        explanationSummary: json['explanation_summary'] as String,
        explanationDetails: (json['explanation_details'] as List).cast<String>(),
        processingTimeMs: (json['processing_time_ms'] as num).toDouble(),
      );
}

class EvidenceSummary {
  final String id;
  final String originalFilename;
  final String sha256Hash;
  final String mimeType;
  final int fileSizeBytes;
  final DateTime uploadedAt;
  final AiResultSummary? aiResult;

  EvidenceSummary({
    required this.id,
    required this.originalFilename,
    required this.sha256Hash,
    required this.mimeType,
    required this.fileSizeBytes,
    required this.uploadedAt,
    this.aiResult,
  });

  factory EvidenceSummary.fromJson(Map<String, dynamic> json) => EvidenceSummary(
        id: json['id'] as String,
        originalFilename: json['original_filename'] as String,
        sha256Hash: json['sha256_hash'] as String,
        mimeType: json['mime_type'] as String,
        fileSizeBytes: json['file_size_bytes'] as int,
        uploadedAt: DateTime.parse(json['uploaded_at'] as String),
        aiResult: json['ai_result'] == null
            ? null
            : AiResultSummary.fromJson(json['ai_result'] as Map<String, dynamic>),
      );
}

class CaseSummary {
  final String id;
  final String caseNumber;
  final String title;
  final String? description;
  final String status;
  final DateTime createdAt;
  final DateTime updatedAt;
  final int evidenceCount;

  CaseSummary({
    required this.id,
    required this.caseNumber,
    required this.title,
    this.description,
    required this.status,
    required this.createdAt,
    required this.updatedAt,
    required this.evidenceCount,
  });

  factory CaseSummary.fromJson(Map<String, dynamic> json) => CaseSummary(
        id: json['id'] as String,
        caseNumber: json['case_number'] as String,
        title: json['title'] as String,
        description: json['description'] as String?,
        status: json['status'] as String,
        createdAt: DateTime.parse(json['created_at'] as String),
        updatedAt: DateTime.parse(json['updated_at'] as String),
        evidenceCount: json['evidence_count'] as int,
      );
}

class CaseDetail extends CaseSummary {
  final List<EvidenceSummary> evidence;

  CaseDetail({
    required super.id,
    required super.caseNumber,
    required super.title,
    super.description,
    required super.status,
    required super.createdAt,
    required super.updatedAt,
    required super.evidenceCount,
    required this.evidence,
  });

  factory CaseDetail.fromJson(Map<String, dynamic> json) => CaseDetail(
        id: json['id'] as String,
        caseNumber: json['case_number'] as String,
        title: json['title'] as String,
        description: json['description'] as String?,
        status: json['status'] as String,
        createdAt: DateTime.parse(json['created_at'] as String),
        updatedAt: DateTime.parse(json['updated_at'] as String),
        evidenceCount: json['evidence_count'] as int,
        evidence: (json['evidence'] as List)
            .map((e) => EvidenceSummary.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class CaseStats {
  final int totalCases;
  final int openCases;
  final int inProgressCases;
  final int closedCases;
  final int archivedCases;
  final int totalEvidence;
  final int cleanVerdicts;
  final int adversarialVerdicts;
  final double? avgConfidence;

  CaseStats({
    required this.totalCases,
    required this.openCases,
    required this.inProgressCases,
    required this.closedCases,
    required this.archivedCases,
    required this.totalEvidence,
    required this.cleanVerdicts,
    required this.adversarialVerdicts,
    this.avgConfidence,
  });

  factory CaseStats.fromJson(Map<String, dynamic> json) => CaseStats(
        totalCases: json['total_cases'] as int,
        openCases: json['open_cases'] as int,
        inProgressCases: json['in_progress_cases'] as int,
        closedCases: json['closed_cases'] as int,
        archivedCases: json['archived_cases'] as int,
        totalEvidence: json['total_evidence'] as int,
        cleanVerdicts: json['clean_verdicts'] as int,
        adversarialVerdicts: json['adversarial_verdicts'] as int,
        avgConfidence: (json['avg_confidence'] as num?)?.toDouble(),
      );
}

class ReportSummary {
  final String id;
  final String caseId;
  final String format;
  final int fileSizeBytes;
  final DateTime createdAt;

  ReportSummary({
    required this.id,
    required this.caseId,
    required this.format,
    required this.fileSizeBytes,
    required this.createdAt,
  });

  factory ReportSummary.fromJson(Map<String, dynamic> json) => ReportSummary(
        id: json['id'] as String,
        caseId: json['case_id'] as String,
        format: json['format'] as String,
        fileSizeBytes: json['file_size_bytes'] as int,
        createdAt: DateTime.parse(json['created_at'] as String),
      );
}

/// The logged-in user's own profile (Module 16). Mirrors backend/app/schemas/auth.py's
/// UserResponse exactly.
class UserProfile {
  final String id;
  final String username;
  final String email;
  final String role;

  UserProfile({required this.id, required this.username, required this.email, required this.role});

  factory UserProfile.fromJson(Map<String, dynamic> json) => UserProfile(
        id: json['id'] as String,
        username: json['username'] as String,
        email: json['email'] as String,
        role: json['role'] as String,
      );
}
