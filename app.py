# app.py
from flask import Flask, render_template
import mysql.connector
import json
import os
from datetime import datetime
from dotenv import load_dotenv

app = Flask(__name__)

# Database configuration

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME', 'homewatch')
}

# Data Dragon base URL for champion images
DDRAGON_BASE_URL = 'https://ddragon.leagueoflegends.com/cdn'

def get_db_connection():
    """Create database connection"""
    return mysql.connector.connect(**DB_CONFIG)

def get_current_rotations():
    """Get the current week's champion rotations"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get the most recent rotation date
        cursor.execute("""
            SELECT MAX(rotation_date) as latest_date 
            FROM champion_rotations
        """)
        latest_date = cursor.fetchone()['latest_date']
        
        if not latest_date:
            return None, None, None
        
        # Get rotation details for the latest date
        cursor.execute("""
            SELECT 
                cr.rotation_date,
                cr.game_version,
                cr.newbie_rotation,
                cr.max_newbie_level,
                c.name as champion_name,
                c.title,
                c.image_full,
                c.champion_key
            FROM champion_rotations cr
            JOIN rotation_champions rc ON cr.id = rc.rotation_id
            JOIN champions c ON rc.champion_id = c.id
            WHERE cr.rotation_date = %s
            ORDER BY cr.newbie_rotation, c.name
        """, (latest_date,))
        
        results = cursor.fetchall()
        
        if not results:
            return None, None, None
        
        # Separate regular and newbie rotations
        regular_rotation = []
        newbie_rotation = []
        rotation_info = {
            'date': latest_date,
            'version': results[0]['game_version']
        }
        
        for row in results:
            champion_data = {
                'name': row['champion_name'],
                'title': row['title'],
                'image_url': f"{DDRAGON_BASE_URL}/{row['game_version'] or rotation_info['version']}/img/champion/{row['image_full']}",
                'champion_key': row['champion_key']
            }
            
            if row['newbie_rotation']:
                newbie_rotation.append(champion_data)
            else:
                regular_rotation.append(champion_data)
        
        return regular_rotation, newbie_rotation, rotation_info
        
    except Exception as e:
        print(f"Database error: {e}")
        return None, None, None
    finally:
        cursor.close()
        conn.close()

@app.route('/')
def index():
    """Main page showing current champion rotations"""
    regular_rotation, newbie_rotation, rotation_info = get_current_rotations()
    
    if not rotation_info:
        return render_template('index.html', 
                             error="No rotation data found",
                             regular_rotation=None,
                             newbie_rotation=None,
                             rotation_info=None)
    
    return render_template('index.html',
                         regular_rotation=regular_rotation,
                         newbie_rotation=newbie_rotation,
                         rotation_info=rotation_info,
                         error=None)

@app.route('/history')
def history():
    """Show historical rotations"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT 
                rotation_date,
                game_version,
                newbie_rotation,
                COUNT(*) as champion_count
            FROM champion_rotations cr
            JOIN rotation_champions rc ON cr.id = rc.rotation_id
            GROUP BY cr.id, rotation_date, game_version, newbie_rotation
            ORDER BY rotation_date DESC, newbie_rotation
        """)
        
        history_data = cursor.fetchall()
        return render_template('history.html', history_data=history_data)
        
    except Exception as e:
        print(f"Database error: {e}")
        return render_template('history.html', history_data=[], error=str(e))
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5005)
