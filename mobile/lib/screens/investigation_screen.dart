import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../api/client.dart';
import '../models/models.dart';
import '../notifications/notification_service.dart';
import '../theme/theme.dart';
import '../widgets/verdict_badge.dart';

class InvestigationScreen extends StatefulWidget {
  final ApiClient api;
  const InvestigationScreen({super.key, required this.api});

  @override
  State<InvestigationScreen> createState() => _InvestigationScreenState();
}

enum _Status { idle, analyzing, done, error }

class _InvestigationScreenState extends State<InvestigationScreen> {
  final _picker = ImagePicker();
  Uint8List? _imageBytes;
  String? _imageFilename;
  _Status _status = _Status.idle;
  AnalysisResult? _result;
  String? _errorMessage;
  final _captionController = TextEditingController();

  Future<void> _pickImage(ImageSource source) async {
    final picked = await _picker.pickImage(source: source, imageQuality: 90);
    if (picked == null) return;
    final bytes = await picked.readAsBytes();
    setState(() {
      _imageBytes = bytes;
      _imageFilename = picked.name;
      _result = null;
      _status = _Status.idle;
      _errorMessage = null;
    });
  }

  Future<void> _analyze() async {
    if (_imageBytes == null) return;
    setState(() => _status = _Status.analyzing);
    try {
      final result = await widget.api.analyzeImage(
        _imageBytes!,
        _imageFilename ?? 'upload.jpg',
        caption: _captionController.text.trim().isEmpty ? null : _captionController.text.trim(),
      );
      setState(() {
        _result = result;
        _status = _Status.done;
      });
      await NotificationService().showAnalysisComplete(
        verdict: result.verdict,
        confidence: result.confidence,
      );
    } catch (e) {
      setState(() {
        _errorMessage = e.toString();
        _status = _Status.error;
      });
    }
  }

  Future<void> _openSaveToCaseSheet() async {
    if (_imageBytes == null || _result == null) return;
    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: TracerColors.panel,
      builder: (context) => _SaveToCaseSheet(
        api: widget.api,
        imageBytes: _imageBytes!,
        imageFilename: _imageFilename ?? 'upload.jpg',
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Investigation')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          GestureDetector(
            onTap: () => _pickImage(ImageSource.gallery),
            child: Container(
              height: 260,
              decoration: BoxDecoration(
                color: TracerColors.panel,
                border: Border.all(color: TracerColors.hairline, style: BorderStyle.solid),
                borderRadius: BorderRadius.circular(10),
              ),
              child: _status == _Status.analyzing
                  ? const Center(child: CircularProgressIndicator())
                  : _imageBytes != null
                      ? ClipRRect(
                          borderRadius: BorderRadius.circular(10),
                          child: Image.memory(_imageBytes!, fit: BoxFit.contain),
                        )
                      : const Center(
                          child: Text('Tap to choose an image',
                              style: TextStyle(color: TracerColors.muted)),
                        ),
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => _pickImage(ImageSource.camera),
                  icon: const Icon(Icons.camera_alt_outlined),
                  label: const Text('Camera'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: OutlinedButton.icon(
                  onPressed: () => _pickImage(ImageSource.gallery),
                  icon: const Icon(Icons.photo_library_outlined),
                  label: const Text('Gallery'),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _captionController,
            decoration: const InputDecoration(
              labelText: 'Expected caption (optional)',
              hintText: 'e.g. a dog playing in a park',
            ),
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: (_imageBytes == null || _status == _Status.analyzing) ? null : _analyze,
            child: Text(_status == _Status.analyzing ? 'Analyzing…' : 'Analyze Image'),
          ),
          if (_status == _Status.error) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: TracerColors.verdictAdversarial.withOpacity(0.1),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(_errorMessage ?? 'Something went wrong.',
                  style: const TextStyle(color: TracerColors.verdictAdversarial)),
            ),
          ],
          if (_status == _Status.done && _result != null) ..._buildResult(_result!),
        ],
      ),
    );
  }

  List<Widget> _buildResult(AnalysisResult result) {
    return [
      const SizedBox(height: 20),
      VerdictBadge(verdict: result.verdict, confidence: result.confidence),
      if (result.attackType != null) ...[
        const SizedBox(height: 12),
        _InfoCard(
          title: 'Attack Type',
          child: Text(
            '${result.attackType!.toUpperCase()} '
            '(${((result.attackTypeConfidence ?? 0) * 100).toStringAsFixed(1)}%)',
            style: const TextStyle(color: TracerColors.verdictWarning, fontSize: 16),
          ),
        ),
      ],
      const SizedBox(height: 12),
      _InfoCard(
        title: 'Attribution Heatmap (${result.attributionMethod})',
        child: ClipRRect(
          borderRadius: BorderRadius.circular(6),
          child: Image.memory(base64Decode(result.attributionHeatmapPngBase64)),
        ),
      ),
      const SizedBox(height: 12),
      _InfoCard(
        title: 'Explainability Panel',
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(result.explanationSummary, style: const TextStyle(color: TracerColors.ink)),
            for (final detail in result.explanationDetails)
              Padding(
                padding: const EdgeInsets.only(top: 6),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('– ', style: TextStyle(color: TracerColors.cyan)),
                    Expanded(child: Text(detail, style: const TextStyle(color: TracerColors.muted, fontSize: 13))),
                  ],
                ),
              ),
          ],
        ),
      ),
      const SizedBox(height: 16),
      OutlinedButton(onPressed: _openSaveToCaseSheet, child: const Text('Save to Case →')),
    ];
  }
}

class _InfoCard extends StatelessWidget {
  final String title;
  final Widget child;
  const _InfoCard({required this.title, required this.child});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: TracerColors.panel,
        border: Border.all(color: TracerColors.hairline),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title.toUpperCase(),
              style: const TextStyle(color: TracerColors.muted, fontSize: 11, letterSpacing: 0.6)),
          const SizedBox(height: 8),
          child,
        ],
      ),
    );
  }
}

class _SaveToCaseSheet extends StatefulWidget {
  final ApiClient api;
  final Uint8List imageBytes;
  final String imageFilename;
  const _SaveToCaseSheet({required this.api, required this.imageBytes, required this.imageFilename});

  @override
  State<_SaveToCaseSheet> createState() => _SaveToCaseSheetState();
}

class _SaveToCaseSheetState extends State<_SaveToCaseSheet> {
  late Future<List<CaseSummary>> _casesFuture;
  String? _selectedCaseId;
  final _newCaseTitleController = TextEditingController();
  bool _saving = false;
  String? _message;
  bool _success = false;

  @override
  void initState() {
    super.initState();
    _casesFuture = widget.api.listCases();
  }

  Future<void> _save() async {
    final usingNewCase = _selectedCaseId == null;
    if (usingNewCase && _newCaseTitleController.text.trim().isEmpty) {
      setState(() => _message = 'Pick an existing case, or enter a title to create a new one.');
      return;
    }
    setState(() {
      _saving = true;
      _message = null;
    });
    try {
      String caseId = _selectedCaseId ?? '';
      String caseLabel = '';
      if (usingNewCase) {
        final created = await widget.api.createCase(title: _newCaseTitleController.text.trim());
        caseId = created.id;
        caseLabel = created.title;
      } else {
        final cases = await _casesFuture;
        caseLabel = cases.firstWhere((c) => c.id == caseId).title;
      }
      await widget.api.attachEvidenceToCase(caseId, widget.imageBytes, widget.imageFilename);
      setState(() {
        _success = true;
        _message = 'Saved to "$caseLabel".';
      });
    } catch (e) {
      setState(() => _message = e.toString());
    } finally {
      setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        left: 16,
        right: 16,
        top: 16,
        bottom: MediaQuery.of(context).viewInsets.bottom + 16,
      ),
      child: FutureBuilder<List<CaseSummary>>(
        future: _casesFuture,
        builder: (context, snapshot) {
          if (!snapshot.hasData) {
            return const SizedBox(height: 120, child: Center(child: CircularProgressIndicator()));
          }
          final cases = snapshot.data!;
          return Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Save to Case', style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                value: _selectedCaseId,
                decoration: const InputDecoration(labelText: 'Existing case'),
                items: [
                  const DropdownMenuItem(value: null, child: Text('— Create a new case instead —')),
                  for (final c in cases)
                    DropdownMenuItem(value: c.id, child: Text('${c.caseNumber} · ${c.title}')),
                ],
                onChanged: _success ? null : (v) => setState(() => _selectedCaseId = v),
              ),
              if (_selectedCaseId == null) ...[
                const SizedBox(height: 12),
                TextField(
                  controller: _newCaseTitleController,
                  enabled: !_success,
                  decoration: const InputDecoration(labelText: 'New case title'),
                ),
              ],
              const SizedBox(height: 16),
              if (!_success)
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _saving ? null : _save,
                    child: Text(_saving ? 'Saving…' : 'Save'),
                  ),
                ),
              if (_message != null) ...[
                const SizedBox(height: 12),
                Text(_message!,
                    style: TextStyle(
                        color: _success ? TracerColors.verdictClean : TracerColors.verdictAdversarial)),
              ],
              if (_success) ...[
                const SizedBox(height: 8),
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text('Done'),
                ),
              ],
            ],
          );
        },
      ),
    );
  }
}
