import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../core/api/api_client.dart';
import '../../../app/theme/app_theme.dart';

class InspectionsScreen extends ConsumerStatefulWidget {
  const InspectionsScreen({super.key});

  @override
  ConsumerState<InspectionsScreen> createState() => _InspectionsScreenState();
}

class _InspectionsScreenState extends ConsumerState<InspectionsScreen> {
  List<dynamic> _inspections = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadInspections();
  }

  Future<void> _loadInspections() async {
    setState(() => _isLoading = true);
    try {
      final apiClient = ApiClient();
      final inspections = await apiClient.getInspections();
      setState(() {
        _inspections = inspections;
        _isLoading = false;
      });
    } catch (e) {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Inspecciones'),
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _inspections.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.search_off, size: 80, color: Colors.grey[400]),
                      const SizedBox(height: 16),
                      Text(
                        'No hay inspecciones',
                        style: TextStyle(fontSize: 18, color: Colors.grey[600]),
                      ),
                      const SizedBox(height: 8),
                      const Text('Crea una inspección desde un proyecto'),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _loadInspections,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _inspections.length,
                    itemBuilder: (context, index) {
                      final inspection = _inspections[index];
                      return Card(
                        margin: const EdgeInsets.only(bottom: 12),
                        child: ListTile(
                          leading: CircleAvatar(
                            backgroundColor: _getStatusColor(inspection['status']).withOpacity(0.1),
                            child: Icon(
                              _getCaptureIcon(inspection['capture_source']),
                              color: _getStatusColor(inspection['status']),
                            ),
                          ),
                          title: Text('Inspección #${inspection['id']}'),
                          subtitle: Text(
                            '${_getCaptureLabel(inspection['capture_source'])} • ${_getStatusLabel(inspection['status'])}',
                          ),
                          trailing: const Icon(Icons.chevron_right),
                          onTap: () => context.go('/inspections/${inspection['id']}'),
                        ),
                      );
                    },
                  ),
                ),
    );
  }

  Color _getStatusColor(String? status) {
    switch (status) {
      case 'completed': return AppTheme.successColor;
      case 'processing': return AppTheme.warningColor;
      case 'failed': return AppTheme.errorColor;
      default: return Colors.grey;
    }
  }

  IconData _getCaptureIcon(String? source) {
    switch (source) {
      case 'dron': return Icons.videocam;
      case 'mobile': return Icons.phone_android;
      case 'combined': return Icons.merge;
      default: return Icons.camera_alt;
    }
  }

  String _getCaptureLabel(String? source) {
    switch (source) {
      case 'dron': return 'Dron';
      case 'mobile': return 'Celular';
      case 'combined': return 'Combinado';
      default: return 'Captura';
    }
  }

  String _getStatusLabel(String? status) {
    switch (status) {
      case 'completed': return 'Completado';
      case 'processing': return 'Procesando';
      case 'failed': return 'Error';
      case 'pending': return 'Pendiente';
      default: return status ?? 'Desconocido';
    }
  }
}
