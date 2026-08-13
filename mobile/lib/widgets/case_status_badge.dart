import 'package:flutter/material.dart';
import '../theme/theme.dart';

class CaseStatusBadge extends StatelessWidget {
  final String status;
  const CaseStatusBadge({super.key, required this.status});

  @override
  Widget build(BuildContext context) {
    final color = caseStatusColor(status);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        border: Border.all(color: color.withOpacity(0.3)),
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        titleCaseStatus(status).toUpperCase(),
        style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.w600, letterSpacing: 0.6),
      ),
    );
  }
}
