<?php

$pdo = new PDO('mysql:host=localhost;dbname=weather;charset=utf8', 'weather', 'PASSWORD');

$datetime = new DateTime();
$datetime->setTime(0, 0, 0);

$stmt = $pdo->prepare("SELECT * FROM temperatures WHERE `date` >= ? ORDER BY `date`");
$stmt->execute([$datetime->format('Y-m-d H:i:s')]);

$temps = $timestamps = $humidities = [];
$data[0] = ['Zeit', 'Temperatur', 'Luftfeuchtigkeit'];

while ($row = $stmt->fetch(PDO::FETCH_ASSOC))
{
    $temps[] = $row['temperature'];
    $timestamps[] = $row['date'];
    $humidities[] = $row['humidity'];

    $data[] = [$row['date'], (float) $row['temperature'], (float) $row['humidity'] / 100];
}

?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="">
    <meta name="author" content="">

    <title>Wetterstation</title>

    <link href="bower_components/bootstrap/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="css/main.css" rel="stylesheet">
</head>

<body>

<div class="container">
    <div class="header clearfix">
        <nav>
            <ul class="nav nav-pills pull-right">
            </ul>
        </nav>
        <h3 class="text-muted">Wetterstation</h3>
    </div>

    <div class="jumbotron">
        <div id="chart_div" style="width: 900px; height: 500px;"></div>
    </div>

    <footer class="footer">

    </footer>

</div>
<!-- /container -->

<script type="text/javascript" src="https://www.google.com/jsapi"></script>
<script type="text/javascript">
    google.load("visualization", "1", {packages: ["corechart"], language: 'de'});
    google.setOnLoadCallback(drawChart);
    function drawChart() {
        var data = google.visualization.arrayToDataTable(<?= json_encode($data); ?>);

        var options = {
            backgroundColor: {fill: 'transparent'},
            title: 'Temperatur/Luftfeuchtigkeit',
            series: {0: {targetAxisIndex: 0}, 1: {targetAxisIndex: 1}},
            vAxes: [
                {
                    title: 'Temperatur',
                    textStyle: {color: 'blue'},
                    format: '#.# °C'
                },
                {
                    title: 'Luftfeuchtigkeit',
                    textStyle: {color: 'red'},
                    format: '#.# %'
                }
            ]
        };

        var chart = new google.visualization.AreaChart(document.getElementById('chart_div'));
        chart.draw(data, options);
    }
</script>

</body>
</html>
