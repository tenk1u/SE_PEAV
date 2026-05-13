import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/api/api_client.dart';
import '../../../app/theme/app_theme.dart';

class ProjectDetailScreen extends ConsumerStatefulWidget {
  final int projectId;
  
  const ProjectDetailScreen({super.key, required this.projectId});

  @override
  ConsumerState<ProjectDetailScreen> createState() => _ProjectDetailScreenState();
}

class _ProjectDetailScreenState extends ConsumerState<ProjectDetailScreen> {
  Map<String, dynamic>? _project;
  List<dynamic> _inspections = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    try {
      final apiClient = ApiClient();
      final project = await apiClient.getProject(widget.projectId);
      final inspections = await apiClient.getInspections(projectId: widget.projectId);
      setState(() {
        _project = project;
        _inspections = inspections;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e'), backgroundColor: AppTheme.errorColor),
        );
      }
    }
  }

  Future<void> _createInspection() async {
    String captureSource = 'dron';
    
    final result = await showDialog<String>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Nueva Inspección'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Selecciona el tipo de captura:'),
            const SizedBox(height: 16),
            ListTile(
              leading: const Icon(Icons.videocam),
              title: const Text('Dron DJI M4E'),
              subtitle: const Text('Captura exterior'),
              onTap: () => Navigator.pop(context, 'dron'),
            ),
            ListTile(
              leading: const Icon(Icons.phone_android),
              title: const Text('Celular'),
              subtitle: const Text('Captura interior'),
              onTap: () => Navigator.pop(context, 'mobile'),
            ),
            ListTile(
              leading: const Icon(Icons.merge),
              title: const Text('Combinado'),
              subtitle: const Text('Dron + Celular'),
              onTap: () => Navigator.pop(context, 'combined'),
            ),
          ],
        ),
      ),
    );

    if (result != null) {
      try {
        final apiClient = ApiClient();
        await apiClient.createInspection(
          projectId: widget.projectId,
          captureSource: result,
        );
        _loadData();
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Inspección creada. Ve a Capturar para subir archivos.'),
              backgroundColor: AppTheme.successColor,
            ),
          );
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Error: $e'), backgroundColor: AppTheme.errorColor),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Scaffold(
        appBar: AppBar(title: const Text('Proyecto')),
        body: const Center(child: CircularProgressIndicator()),
      );
    }

    if (_project == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Proyecto')),
        body: const Center(child: Text('Proyecto no encontrado')),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: Text(_project!['name'] ?? 'Proyecto'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Project info card
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: AppTheme.primaryColor.withOpacity(0.1),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: const Icon(
                            Icons.folder,
                            color: AppTheme.primaryColor,
                            size: 32,
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                _project!['name'] ?? '',
                                style: const TextStyle(
                                  fontSize: 20,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              if (_project!['address'] != null) ...[
                                const SizedBox(height: 4),
                                Text(
                                  _project!['address'],
                                  style: TextStyle(color: Colors.grey[600]),
                                ),
                              ],
                            ],
                          ),
                        ),
                      ],
                    ),
                    if (_project!['description'] != null) ...[
                      const SizedBox(height: 16),
                      Text(
                        _project!['description'],
                        style: TextStyle(color: Colors.grey[700]),
                      ),
                    ],
                    if (_project!['latitude'] != null && _project!['longitude'] != null) ...[
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          const Icon(Icons.location_on, size: 16, color: Colors.grey),
                          const SizedBox(width: 4),
                          Text(
                            '${_project!['latitude']}, ${_project!['longitude']}',
                            style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                          ),
                        ],
                      ),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // Inspections section
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Inspecciones',
                  style: Theme.of(context).textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                ElevatedButton.icon(
                  onPressed: _createInspection,
                  icon: const Icon(Icons.add, size: 18),
                  label: const Text('Nueva'),
                ),
              ],
            ),
            const SizedBox(height: 12),

            if (_inspections.isEmpty)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(32),
                  child: Center(
                    child: Column(
                      children: [
                        Icon(Icons.search_off, size: 48, color: Colors.grey[400]),
                        const SizedBox(height: 12),
                        Text(
                          'No hay inspecciones',
                          style: TextStyle(color: Colors.grey[600]),
                        ),
                        const SizedBox(height: 8),
                        const Text('Crea una inspección para empezar'),
                      ],
                    ),
                  ),
                ),
              )
            else
              ...List.generate(_inspections.length, (index) {
                final inspection = _inspections[index];
                return _InspectionCard(
                  inspection: inspection,
                  onTap: () => context.go('/inspections/${inspection['id']}'),
                );
              }),
          ],
        ),
      ),
    );
  }
}

class _InspectionCard extends StatelessWidget {
  final Map<String, dynamic> inspection;
  final VoidCallback onTap;

  const _InspectionCard({
    required this.inspection,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final status = inspection['status'] ?? 'pending';
    final captureSource = inspection['capture_source'] ?? 'unknown';
    
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: _getStatusColor(status).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(
                  _getCaptureIcon(captureSource),
                  color: _getStatusColor(status),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Inspección #${inspection['id']}',
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      _getCaptureLabel(captureSource),
                      style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: _getStatusColor(status).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  _getStatusLabel(status),
                  style: TextStyle(
                    fontSize: 12,
                    color: _getStatusColor(status),
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Color _getStatusColor(String status) {
    switch (status) {
      case 'completed': return AppTheme.successColor;
      case 'processing': return AppTheme.warningColor;
      case 'failed': return AppTheme.errorColor;
      default: return Colors.grey;
    }
  }

  IconData _getCaptureIcon(String source) {
    switch (source) {
      case 'dron': return Icons.videocam;
      case 'mobile': return Icons.phone_android;
      case 'combined': return Icons.merge;
      default: return Icons.camera_alt;
    }
  }

  String _getCaptureLabel(String source) {
    switch (source) {
      case 'dron': return 'Captura con dron';
      case 'mobile': return 'Captura con celular';
      case 'combined': return 'Captura combinada';
      default: return 'Captura';
    }
  }

  String _getStatusLabel(String status) {
    switch (status) {
      case 'completed': return 'Completado';
      case 'processing': return 'Procesando';
      case 'failed': return 'Error';
      case 'pending': return 'Pendiente';
      default: return status;
    }
  }
}
