import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from urllib.parse import urlparse, parse_qs
import re
from collections import Counter
import warnings
warnings.filterwarnings('ignore')

# Configurar estilo de gráficos
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def load_and_clean_data(file_path):
    """
    Carga y limpia los datos del CSV
    """
    # Leer CSV
    df = pd.read_csv(file_path)
    
    # Limpiar URLs - extraer solo la parte del endpoint después de 8010/
    df['clean_endpoint'] = df['url'].str.replace(r'http://localhost:8010/api/', '', regex=True)
    
    # Convertir tiempo de respuesta a milisegundos para mejor legibilidad
    df['response_time_ms'] = df['average_time'] * 1000
    
    # Extraer información adicional de los endpoints
    df['base_endpoint'] = df['clean_endpoint'].apply(extract_base_endpoint)
    df['endpoint_type'] = df['clean_endpoint'].apply(categorize_endpoint)
    df['has_parameters'] = df['clean_endpoint'].str.contains(r'\?')
    df['keyword'] = df['clean_endpoint'].apply(extract_keyword)
    df['endpoint_depth'] = df['clean_endpoint'].str.count('/') + 1
    
    return df

def extract_base_endpoint(endpoint):
    """Extrae el endpoint base sin parámetros"""
    return endpoint.split('?')[0]

def categorize_endpoint(endpoint):
    """Categoriza el tipo de endpoint"""
    if 'search' in endpoint:
        return 'search'
    elif 'person' in endpoint and 'apc' not in endpoint:
        return 'person'
    elif 'affiliation' in endpoint and 'apc' not in endpoint:
        return 'affiliation'
    elif 'apc' in endpoint:
        return 'apc'
    else:
        return 'other'

def extract_keyword(endpoint):
    """Extrae keywords de los parámetros de búsqueda"""
    if 'keywords=' in endpoint:
        try:
            keyword = endpoint.split('keywords=')[1].split('&')[0]
            return keyword
        except:
            return None
    return None

def basic_statistics(df):
    """
    Calcula estadísticas básicas de los tiempos de respuesta
    """
    stats = {
        'total_requests': len(df),
        'unique_endpoints': df['base_endpoint'].nunique(),
        'avg_response_time': df['average_time'].mean(),
        'median_response_time': df['average_time'].median(),
        'std_response_time': df['average_time'].std(),
        'min_response_time': df['average_time'].min(),
        'max_response_time': df['average_time'].max(),
        'p95_response_time': df['average_time'].quantile(0.95),
        'p99_response_time': df['average_time'].quantile(0.99)
    }
    
    return stats

def endpoint_analysis(df):
    """
    Analiza performance por endpoint
    """
    # Agrupar por endpoint base
    endpoint_stats = df.groupby('base_endpoint').agg({
        'average_time': ['count', 'mean', 'median', 'std', 'min', 'max'],
        'response_time_ms': ['mean', 'max']
    }).round(4)
    
    # Aplanar nombres de columnas
    endpoint_stats.columns = ['call_count', 'avg_time', 'median_time', 'std_time', 
                             'min_time', 'max_time', 'avg_time_ms', 'max_time_ms']
    
    # Ordenar por tiempo promedio descendente
    endpoint_stats = endpoint_stats.sort_values('avg_time', ascending=False)
    
    return endpoint_stats

def keyword_analysis(df):
    """
    Analiza performance por keyword de búsqueda
    """
    # Filtrar solo requests con keywords
    search_df = df[df['keyword'].notna()].copy()
    
    if len(search_df) == 0:
        return pd.DataFrame()
    
    keyword_stats = search_df.groupby('keyword').agg({
        'average_time': ['count', 'mean', 'median', 'min', 'max'],
        'response_time_ms': 'mean'
    }).round(4)
    
    keyword_stats.columns = ['search_count', 'avg_time', 'median_time', 
                           'min_time', 'max_time', 'avg_time_ms']
    
    return keyword_stats.sort_values('avg_time', ascending=False)

def endpoint_type_analysis(df):
    """
    Analiza performance por tipo de endpoint
    """
    type_stats = df.groupby('endpoint_type').agg({
        'average_time': ['count', 'mean', 'median', 'std', 'min', 'max']
    }).round(4)
    
    type_stats.columns = ['request_count', 'avg_time', 'median_time', 
                         'std_time', 'min_time', 'max_time']
    
    return type_stats.sort_values('avg_time', ascending=False)

def find_slowest_endpoints(df, n=10):
    """
    Encuentra los endpoints más lentos
    """
    slowest = df.nlargest(n, 'average_time')[['clean_endpoint', 'average_time', 'response_time_ms']]
    return slowest

def response_time_distribution(df):
    """
    Analiza la distribución de tiempos de respuesta
    """
    # Definir rangos de tiempo
    bins = [0, 0.05, 0.1, 0.5, 1.0, 5.0, float('inf')]
    labels = ['0-50ms', '50-100ms', '100-500ms', '500ms-1s', '1-5s', '5s+']
    
    df['time_range'] = pd.cut(df['average_time'], bins=bins, labels=labels, right=False)
    
    distribution = df['time_range'].value_counts().sort_index()
    return distribution

def create_visualizations(df, stats, endpoint_stats, keyword_stats, type_stats):
    """
    Crea visualizaciones de los datos
    """
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    fig.suptitle('Análisis de Performance API', fontsize=16, fontweight='bold')
    
    # 1. Distribución de tiempos de respuesta
    axes[0, 0].hist(df['response_time_ms'], bins=50, alpha=0.7, color='skyblue', edgecolor='black')
    axes[0, 0].set_title('Distribución de Tiempos de Respuesta')
    axes[0, 0].set_xlabel('Tiempo (ms)')
    axes[0, 0].set_ylabel('Frecuencia')
    axes[0, 0].axvline(stats['avg_response_time']*1000, color='red', linestyle='--', 
                       label=f'Media: {stats["avg_response_time"]*1000:.1f}ms')
    axes[0, 0].legend()
    
    # 2. Top 10 endpoints más lentos
    top_endpoints = endpoint_stats.head(10)
    axes[0, 1].barh(range(len(top_endpoints)), top_endpoints['avg_time_ms'])
    axes[0, 1].set_yticks(range(len(top_endpoints)))
    axes[0, 1].set_yticklabels([ep[:30] + '...' if len(ep) > 30 else ep 
                               for ep in top_endpoints.index], fontsize=8)
    axes[0, 1].set_title('Top 10 Endpoints Más Lentos')
    axes[0, 1].set_xlabel('Tiempo Promedio (ms)')
    
    # 3. Performance por tipo de endpoint
    axes[0, 2].bar(type_stats.index, type_stats['avg_time'] * 1000)
    axes[0, 2].set_title('Tiempo Promedio por Tipo de Endpoint')
    axes[0, 2].set_xlabel('Tipo de Endpoint')
    axes[0, 2].set_ylabel('Tiempo Promedio (ms)')
    axes[0, 2].tick_params(axis='x', rotation=45)
    
    # 4. Número de llamadas por endpoint
    call_counts = endpoint_stats['call_count'].head(10)
    axes[1, 0].bar(range(len(call_counts)), call_counts.values)
    axes[1, 0].set_title('Top 10 Endpoints Más Llamados')
    axes[1, 0].set_xlabel('Endpoints')
    axes[1, 0].set_ylabel('Número de Llamadas')
    axes[1, 0].set_xticks(range(len(call_counts)))
    axes[1, 0].set_xticklabels([ep[:15] + '...' if len(ep) > 15 else ep 
                               for ep in call_counts.index], rotation=45, fontsize=8)
    
    # 5. Keywords más lentas (si existen)
    if not keyword_stats.empty:
        top_keywords = keyword_stats.head(8)
        axes[1, 1].barh(range(len(top_keywords)), top_keywords['avg_time_ms'])
        axes[1, 1].set_yticks(range(len(top_keywords)))
        axes[1, 1].set_yticklabels(top_keywords.index, fontsize=10)
        axes[1, 1].set_title('Keywords de Búsqueda Más Lentas')
        axes[1, 1].set_xlabel('Tiempo Promedio (ms)')
    else:
        axes[1, 1].text(0.5, 0.5, 'No hay datos de keywords', 
                       ha='center', va='center', transform=axes[1, 1].transAxes)
        axes[1, 1].set_title('Keywords de Búsqueda')
    
    # 6. Box plot de tiempos por tipo
    df_plot = df[df['response_time_ms'] < df['response_time_ms'].quantile(0.95)]  # Excluir outliers extremos
    sns.boxplot(data=df_plot, x='endpoint_type', y='response_time_ms', ax=axes[1, 2])
    axes[1, 2].set_title('Distribución de Tiempos por Tipo (sin outliers extremos)')
    axes[1, 2].set_xlabel('Tipo de Endpoint')
    axes[1, 2].set_ylabel('Tiempo (ms)')
    axes[1, 2].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    return fig

def generate_report(df, stats, endpoint_stats, keyword_stats, type_stats, slowest):
    """
    Genera un reporte textual completo
    """
    report = []
    report.append("="*70)
    report.append("REPORTE DE ANÁLISIS DE PERFORMANCE API")
    report.append("="*70)
    
    # Estadísticas generales
    report.append("\n📊 ESTADÍSTICAS GENERALES:")
    report.append(f"  • Total de requests: {stats['total_requests']:,}")
    report.append(f"  • Endpoints únicos: {stats['unique_endpoints']:,}")
    report.append(f"  • Tiempo promedio: {stats['avg_response_time']*1000:.2f} ms")
    report.append(f"  • Tiempo mediano: {stats['median_response_time']*1000:.2f} ms")
    report.append(f"  • Desviación estándar: {stats['std_response_time']*1000:.2f} ms")
    report.append(f"  • Tiempo mínimo: {stats['min_response_time']*1000:.2f} ms")
    report.append(f"  • Tiempo máximo: {stats['max_response_time']*1000:.2f} ms")
    report.append(f"  • Percentil 95: {stats['p95_response_time']*1000:.2f} ms")
    report.append(f"  • Percentil 99: {stats['p99_response_time']*1000:.2f} ms")
    
    # Top endpoints más lentos
    report.append(f"\n🐌 TOP {len(slowest)} ENDPOINTS MÁS LENTOS:")
    for i, (_, row) in enumerate(slowest.iterrows(), 1):
        report.append(f"  {i:2d}. {row['clean_endpoint'][:60]}{'...' if len(row['clean_endpoint']) > 60 else ''}")
        report.append(f"      Tiempo: {row['response_time_ms']:.2f} ms")
    
    # Performance por tipo
    report.append(f"\n🏷️  PERFORMANCE POR TIPO DE ENDPOINT:")
    for endpoint_type, row in type_stats.iterrows():
        report.append(f"  • {endpoint_type.upper()}:")
        report.append(f"    - Requests: {row['request_count']:,}")
        report.append(f"    - Tiempo promedio: {row['avg_time']*1000:.2f} ms")
        report.append(f"    - Tiempo mediano: {row['median_time']*1000:.2f} ms")
    
    # Top endpoints por número de llamadas
    report.append(f"\n📞 TOP 10 ENDPOINTS MÁS LLAMADOS:")
    top_called = endpoint_stats.sort_values('call_count', ascending=False).head(10)
    for i, (endpoint, row) in enumerate(top_called.iterrows(), 1):
        report.append(f"  {i:2d}. {endpoint[:50]}{'...' if len(endpoint) > 50 else ''}")
        report.append(f"      Llamadas: {row['call_count']:,}, Tiempo promedio: {row['avg_time_ms']:.2f} ms")
    
    # Keywords analysis si existe
    if not keyword_stats.empty:
        report.append(f"\n🔍 ANÁLISIS DE KEYWORDS DE BÚSQUEDA:")
        report.append(f"  Total de búsquedas: {keyword_stats['search_count'].sum():,}")
        report.append(f"  Keywords únicas: {len(keyword_stats)}")
        report.append(f"\n  Top keywords más lentas:")
        for i, (keyword, row) in enumerate(keyword_stats.head(5).iterrows(), 1):
            report.append(f"    {i}. '{keyword}': {row['avg_time_ms']:.2f} ms promedio ({row['search_count']} búsquedas)")
    
    # Distribución de tiempos
    distribution = response_time_distribution(df)
    report.append(f"\n⏱️  DISTRIBUCIÓN DE TIEMPOS DE RESPUESTA:")
    for time_range, count in distribution.items():
        percentage = (count / len(df)) * 100
        report.append(f"  • {time_range}: {count:,} requests ({percentage:.1f}%)")
    
    # Recomendaciones
    report.append(f"\n💡 RECOMENDACIONES:")
    
    # Endpoints problemáticos
    slow_endpoints = endpoint_stats[endpoint_stats['avg_time'] > stats['avg_response_time'] * 2].head(5)
    if not slow_endpoints.empty:
        report.append(f"  🚨 Endpoints que requieren optimización (>2x promedio):")
        for endpoint, row in slow_endpoints.iterrows():
            report.append(f"    - {endpoint}: {row['avg_time_ms']:.2f} ms promedio")
    
    # Keywords problemáticas
    if not keyword_stats.empty:
        slow_keywords = keyword_stats[keyword_stats['avg_time_ms'] > 1000].head(3)
        if not slow_keywords.empty:
            report.append(f"  🔍 Keywords de búsqueda problemáticas (>1s):")
            for keyword, row in slow_keywords.iterrows():
                report.append(f"    - '{keyword}': {row['avg_time_ms']:.2f} ms")
    
    # Estadísticas por profundidad
    depth_stats = df.groupby('endpoint_depth')['average_time'].agg(['count', 'mean']).round(4)
    worst_depth = depth_stats.loc[depth_stats['mean'].idxmax()]
    report.append(f"  📊 Profundidad de endpoint más lenta: {depth_stats['mean'].idxmax()} niveles ({worst_depth['mean']*1000:.2f} ms promedio)")
    
    return "\n".join(report)

def save_results(df, stats, endpoint_stats, keyword_stats, type_stats, slowest, distribution):
    """
    Guarda los resultados en archivos CSV
    """
    # Datos limpios
    df.to_csv('api_data_clean.csv', index=False)
    
    # Estadísticas por endpoint
    endpoint_stats.to_csv('endpoint_performance_stats.csv')
    
    # Keywords stats
    if not keyword_stats.empty:
        keyword_stats.to_csv('keyword_performance_stats.csv')
    
    # Endpoints más lentos
    slowest.to_csv('slowest_endpoints.csv', index=False)
    
    # Estadísticas por tipo
    type_stats.to_csv('endpoint_type_stats.csv')
    
    print("✅ Archivos guardados:")
    print("  - api_data_clean.csv")
    print("  - endpoint_performance_stats.csv")
    if not keyword_stats.empty:
        print("  - keyword_performance_stats.csv")
    print("  - slowest_endpoints.csv")
    print("  - endpoint_type_stats.csv")

def main():
    """
    Función principal que ejecuta todo el análisis
    """
    # Cargar datos (cambiar por la ruta de tu archivo)
    file_path = 'api_response_times.csv'  # Cambiar por tu archivo
    
    print("🔄 Cargando y limpiando datos...")
    df = load_and_clean_data(file_path)
    
    print("📊 Calculando estadísticas...")
    stats = basic_statistics(df)
    endpoint_stats = endpoint_analysis(df)
    keyword_stats = keyword_analysis(df)
    type_stats = endpoint_type_analysis(df)
    slowest = find_slowest_endpoints(df, 15)
    distribution = response_time_distribution(df)
    
    print("📈 Generando visualizaciones...")
    fig = create_visualizations(df, stats, endpoint_stats, keyword_stats, type_stats)
    plt.savefig('api_performance_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print("📋 Generando reporte...")
    report = generate_report(df, stats, endpoint_stats, keyword_stats, type_stats, slowest)
    
    # Guardar reporte en archivo
    with open('api_performance_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n💾 Guardando resultados...")
    save_results(df, stats, endpoint_stats, keyword_stats, type_stats, slowest, distribution)
    
    print(f"\n✅ Análisis completado!")
    print(f"  - Gráfico guardado: api_performance_analysis.png")
    print(f"  - Reporte guardado: api_performance_report.txt")

if __name__ == "__main__":
    main()