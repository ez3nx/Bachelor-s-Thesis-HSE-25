import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


def plot_daily_posts(daily_counts, ticker):
    # Линия тренда
    x = np.arange(len(daily_counts))
    y = daily_counts["count"]
    coefficients = np.polyfit(x, y, 1)
    trend_line = np.polyval(coefficients, x)

    # Создание фигуры
    fig = go.Figure()

    # Добавление точек и линии
    fig.add_trace(
        go.Scatter(
            x=daily_counts["inserted"],
            y=daily_counts["count"],
            mode="lines+markers",
            name="Публикации",
            line=dict(color="#FF6B6B", width=2),
            marker=dict(size=4, color="#FF6B6B"),
        )
    )

    # Добавление линии тренда
    fig.add_trace(
        go.Scatter(
            x=daily_counts["inserted"],
            y=trend_line,
            mode="lines",
            name="Тренд",
            line=dict(color="black", width=2, dash="dash"),
        )
    )

    # Настройка макета
    fig.update_layout(
        title={
            "text": f"Динамика публикаций по дням {ticker}",
            "y": 0.95,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": dict(size=20),
        },
        xaxis_title="Дата",
        yaxis_title="Количество публикаций",
        template="plotly_white",
        hovermode="x unified",
        showlegend=True,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    )

    # Настройка осей
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="LightGray")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="LightGray")

    fig.show()


def plot_posts_length(df, ticker, col, x_label):
    # Установка стиля
    plt.style.use("seaborn")
    sns.set_palette("husl")

    # Создание графика
    plt.figure(figsize=(6, 3))
    sns.histplot(data=df, x=col, bins=20, color="#2ecc71")

    # Кастомизация
    plt.title(f"Distribution of post lengths {ticker}", fontsize=13, pad=15)
    plt.xlabel(f"{x_label}", fontsize=11)
    plt.ylabel("Count", fontsize=11)

    # Удаление верхней и правой границы
    sns.despine()

    # Добавление сетки
    plt.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()
