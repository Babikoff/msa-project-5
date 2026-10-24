using Dapper;
using Npgsql;

Console.WriteLine("Staring...");

var dbConnectionString = Environment.GetEnvironmentVariable("LOGISTICS_DB_CONNECTION_STRING")
    ?? throw new ArgumentException("LOGISTICS_DB_CONNECTION_STRING not set");
var outputPath = Environment.GetEnvironmentVariable("OUTPUT_PATH")
    ?? throw new ArgumentException("OUTPUT_PATH not set");

Directory.CreateDirectory(outputPath);
await using var connection = new NpgsqlConnection(dbConnectionString);
await connection.OpenAsync();

var outputFile = outputPath + "report.csv";

Console.WriteLine("Staring data job");

var report = await connection.QueryAsync<ReportRecord>(
@"
select
    c.id ClientId,
    c.name as ClientName,
    d.full_name as DriverFullName,
    v.descr as Car,
    v.reg_num as CarNumber,
    s.source_location SourceLocation,
    s.dest_location DestinationLocation,
    s.scheduled_start ScheduledStart,
    s.scheduled_finish ScheduledFinish,
    se.""event"" EventType,
    se.event_time EventTime,
    se.descr EventDescription
from shipments s
left join clients c on c.id = s.client_id
full join vehicles v on v.id = s.vehicle_id
full join drivers d on d.id = s.driver_id
left join shipment_events se on se.shipment_id = s.id
order by c.id, s.scheduled_start, se.event_time, d.full_name"
);

var count = 0;
using (var sw = new StreamWriter(outputFile)) {
    await sw.WriteLineAsync($"ClientId,ClientName,DriverFullName,Car,SourceLocation,DestinationLocation," +
        $"ScheduledStart,ScheduledFinish,EventType,EventTime,EventDescription");

    foreach (var r in report)
    {
        await sw.WriteLineAsync($"{r.ClientId},{r.ClientName},{r.DriverFullName},{r.Car},{r.SourceLocation},{r.DestinationLocation}," +
            $"{r.ScheduledStart},{r.ScheduledFinish},{r.EventType},{r.EventTime},{r.EventDescription}");
        count++;
    }
}

Console.WriteLine($"Finished. Number of records created: {count}");

record ReportRecord(
    long ClientId,
    string ClientName,
    string DriverFullName,
    string Car,
    string CarNumber,
    string SourceLocation,
    string DestinationLocation,
    DateTime ScheduledStart,
    DateTime ScheduledFinish,
    string EventType,
    DateTime EventTime,
    string EventDescription
    );
