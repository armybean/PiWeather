<?php

if ( ! is_readable('config.php'))
{
    die('No configuration file found. Please rename sample_config.php to config.php and edit the value to fit your setup.');
}

require_once 'config.php';
$db = $config['Database'];

$pdo = new PDO('mysql:host=' . $db['host'] . ';dbname=' . $db['database'] . ';charset=utf8', $db['user'],
    $db['password']);

// Select all dates
$stmt = $pdo->prepare("SELECT DISTINCT DATE_FORMAT(`date`, '%d.%m.%Y') AS d FROM temperatures ORDER BY `date` DESC");
$stmt->execute();
$dates = $stmt->fetchAll(PDO::FETCH_ASSOC);

$datetime = (isset($_POST['date']))
    ? DateTime::createFromFormat('d.m.Y', $_POST['date'])
    : new DateTime();
$datetime->setTime(0, 0, 0);

$stmt =
    $pdo->prepare("SELECT * FROM temperatures WHERE `date` >= :d AND `date` < DATE_ADD(:d, INTERVAL 1 DAY) ORDER BY `date`");
$stmt->execute([':d' => $datetime->format('Y-m-d H:i:s')]);

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
<html lang="de">
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
        <h3 class="text-muted pull-left">Wetterstation</h3>

        <form action="index.php" method="post" class="form-inline pull-right">
            <div class="form-group">
                <select name="date" id="date" class="form-control">
                    <?php foreach ($dates as $date): ?>
                        <option value="<?= $date['d']; ?>" <?= ($datetime->format('d.m.Y') == $date['d']) ? 'selected'
                            : ''; ?>><?= $date['d']; ?></option>
                    <?php endforeach; ?>
                </select>
            </div>
            <button class="btn btn-primary" type="submit">Datum ändern</button>
        </form>
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
