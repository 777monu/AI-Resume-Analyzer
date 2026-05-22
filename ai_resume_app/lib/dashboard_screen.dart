import 'package:flutter/material.dart';
import 'analyze_screen.dart';
import 'history_screen.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],

      appBar: AppBar(
        title: Text("Dashboard"),
        centerTitle: true,
        actions: [
          IconButton(
            icon: Icon(Icons.logout),
            onPressed: () {
              Navigator.pushAndRemoveUntil(
                context,
                MaterialPageRoute(builder: (context) => DashboardScreen()),
                (route) => false,
              );
            },
          )
        ],
      ),

      body: Padding(
        padding: EdgeInsets.all(20),
        child: Column(
          children: [

            SizedBox(height: 20),

            // ANALYZE RESUME CARD
            _buildCard(
              context,
              title: "Analyze Resume",
              icon: Icons.analytics,
              color: Colors.blue,
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                   builder: (context) => AnalyzeScreen(),
                  ),
                );
              },
            ),

            SizedBox(height: 15),

            // HISTORY CARD
            _buildCard(
              context,
              title: "History",
              icon: Icons.history,
              color: Colors.green,
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (context) => HistoryScreen(),
                  ),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCard(BuildContext context,
      {required String title,
      required IconData icon,
      required Color color,
      required VoidCallback onTap}) {
    return InkWell(
      onTap: onTap,
      child: Container(
        width: double.infinity,
        padding: EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: color,
          borderRadius: BorderRadius.circular(15),
        ),
        child: Row(
          children: [
            Icon(icon, color: Colors.white, size: 40),
            SizedBox(width: 15),
            Text(
              title,
              style: TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
          ],
        ),
      ),
    );
  }
}