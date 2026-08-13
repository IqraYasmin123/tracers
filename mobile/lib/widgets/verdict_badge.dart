import 'package:flutter/material.dart';
import '../theme/theme.dart';

class VerdictBadge extends StatelessWidget {
  final String? verdict;
  final double? confidence;

  const VerdictBadge({super.key, required this.verdict, required this.confidence});

  @override
  Widget build(BuildContext context) {
    final color = verdictColor(verdict);
    final confidenceText =
        confidence == null ? '—' : '${(confidence! * 100).toStringAsFixed(1)}%';
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        border: Border.all(color: color.withOpacity(0.3)),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            (verdict ?? 'unknown').toUpperCase(),
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.bold,
              fontSize: 16,
              letterSpacing: 1.1,
            ),
          ),
          Text('$confidenceText confidence',
              style: const TextStyle(color: TracerColors.muted, fontSize: 13)),
        ],
      ),
    );
  }
}
