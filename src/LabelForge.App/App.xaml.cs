namespace LabelForge.App;

using System.Windows;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using LabelForge.Core.Serialization;
using LabelForge.Core.Validation;

public partial class App : Application
{
    private IHost? _host;

    public static IHost Host => ((App)Current)._host!;

    private async void OnStartup(object sender, StartupEventArgs e)
    {
        _host = Microsoft.Extensions.Hosting.Host.CreateDefaultBuilder(e.Args)
            .ConfigureServices((context, services) =>
            {
                // Register Core services
                services.AddSingleton<DocumentSerializer>();
                services.AddSingleton<DocumentValidator>();
                services.AddSingleton<AtomicFileOperations>();

                // Register Main Window & ViewModels
                services.AddSingleton<MainWindow>();
            })
            .ConfigureLogging(logging =>
            {
                logging.ClearProviders();
                logging.AddConsole();
                logging.AddDebug();
            })
            .Build();

        await _host.StartAsync();

        var mainWindow = _host.Services.GetRequiredService<MainWindow>();
        mainWindow.Show();
    }

    private async void OnExit(object sender, ExitEventArgs e)
    {
        if (_host != null)
        {
            await _host.StopAsync();
            _host.Dispose();
        }
    }
}
