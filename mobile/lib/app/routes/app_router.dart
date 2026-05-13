import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../core/api/api_client.dart';
import '../../features/auth/presentation/login_screen.dart';
import '../../features/auth/presentation/register_screen.dart';
import '../../features/projects/presentation/projects_screen.dart';
import '../../features/projects/presentation/project_detail_screen.dart';
import '../../features/inspections/presentation/inspections_screen.dart';
import '../../features/inspections/presentation/inspection_detail_screen.dart';
import '../../features/capture/presentation/capture_screen.dart';
import '../../features/reports/presentation/reports_screen.dart';
import '../../features/reports/presentation/report_viewer_screen.dart';
import '../../shared/widgets/main_scaffold.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  return GoRouter(
    initialLocation: '/login',
    debugLogDiagnostics: true,
    routes: [
      // Auth routes
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register',
        builder: (context, state) => const RegisterScreen(),
      ),
      
      // Main app with bottom navigation
      ShellRoute(
        builder: (context, state, child) => MainScaffold(child: child),
        routes: [
          GoRoute(
            path: '/projects',
            builder: (context, state) => const ProjectsScreen(),
            routes: [
              GoRoute(
                path: ':id',
                builder: (context, state) => ProjectDetailScreen(
                  projectId: int.parse(state.pathParameters['id']!),
                ),
              ),
            ],
          ),
          GoRoute(
            path: '/inspections',
            builder: (context, state) => const InspectionsScreen(),
            routes: [
              GoRoute(
                path: ':id',
                builder: (context, state) => InspectionDetailScreen(
                  inspectionId: int.parse(state.pathParameters['id']!),
                ),
              ),
            ],
          ),
          GoRoute(
            path: '/capture',
            builder: (context, state) => const CaptureScreen(),
          ),
          GoRoute(
            path: '/reports',
            builder: (context, state) => const ReportsScreen(),
            routes: [
              GoRoute(
                path: ':id',
                builder: (context, state) => ReportViewerScreen(
                  reportId: int.parse(state.pathParameters['id']!),
                ),
              ),
            ],
          ),
        ],
      ),
    ],
    redirect: (context, state) async {
      final apiClient = ApiClient();
      final isLoggedIn = await apiClient.isLoggedIn();
      final isAuthRoute = state.matchedLocation == '/login' || 
                          state.matchedLocation == '/register';
      
      if (!isLoggedIn && !isAuthRoute) {
        return '/login';
      }
      
      if (isLoggedIn && isAuthRoute) {
        return '/projects';
      }
      
      return null;
    },
  );
});
