use Test::More;
use Test::Exception;
use Try::Tiny;
use List::MoreUtils qw/uniq/;
use File::Spec;
use Set::Scalar;
use lib '../lib';
use Log::Log4perl::Level;
use Bento::MakeModel;
my $samplesd = File::Spec->catdir( (-d 't' ? 't' : '.'), 'samples' );
my (@n, @r);

my $NUMNODES=29;
my $NUMNUTS=0;
my $NUMEDGES=36;
my $NUMPROPS=186;
my $NUMETYPES=15;

my $obj = Bento::MakeModel->new(
    LOG_LEVEL=>$INFO,
    files => [ File::Spec->catdir($samplesd,"icdc-model.yml"), File::Spec->catdir($samplesd,"icdc-model-props.yml") ]
   );

my $model = $obj->model;

is scalar ($model->nodes), $NUMNODES, "count nodes";
is scalar ($model->props), $NUMPROPS, "count all props";
is scalar ($model->edge_types), $NUMETYPES, "count all edge types";
is scalar ($model->edges), $NUMEDGES, "count all edges";

my $tbl;
open my $fh, ">", \$tbl;
ok $obj->table($fh), 'make table';

my (@nodes,@relns);
my $rel;
for my $line (split /\n/,$tbl) {
  my @d = split /\t/, $line;
  next unless $d[0];
  next if ($d[0] =~ /^node$/);
  if ($d[0] =~ /^relationship$/) {
    $rel = 1;
    next;
  }
  if ($rel) {
    push @relns, \@d;
  }
  else {
    push @nodes, \@d;
  }
}

my $got_nodes = Set::Scalar->new(map { $$_[0] } @nodes);
my $got_props = Set::Scalar->new((map { $$_[1] } @nodes), (map {$$_[3]} @relns));
$got_props->delete('NA');
my $got_etypes = Set::Scalar->new(map { $$_[0] } @relns);
my $exp_nodes = Set::Scalar->new(map {$_->name} $model->nodes);
my $exp_props = Set::Scalar->new(map {$_->name} $model->props);
my $exp_etypes = Set::Scalar->new(map {$_->name} $model->edge_types);

# is scalar (uniq map { $$_[0] } @nodes), $NUMNODES, "nodes correct";
# is scalar (uniq  map { $$_[1] } @nodes), $NUMPROPS, "props correct";
# is scalar @relns, $NUMEDGES, "edges correct";
# is scalar (uniq map {$$_[0]} @relns), $NUMETYPES, "edge types correct";

if ($got_nodes->is_equal($exp_nodes)) {
  pass "nodes correct (".$got_nodes->size.")";
}
else {
  fail "nodes incorrect";
  diag "got ".$got_nodes->size.", expected ".$exp_nodes->size;
  diag "symmetric difference";
  diag join("\n", $got_nodes->symmetric_difference($exp_nodes)->members);
}

if ($got_props->is_equal($exp_props)) {
  pass "props correct (".$got_props->size.")";
}
else {
  fail "props incorrect";
  diag "got ".$got_props->size.", expected ".$exp_props->size;
  diag "symmetric difference";
  diag join("\n", $got_props->symmetric_difference($exp_props)->members);
}

if ($got_etypes->is_equal($exp_etypes)) {
  pass "edge types correct (".$got_etypes->size.")";
}
else {
  fail "edge types incorrect";
  diag "got ".$got_etypes->size.", expected ".$exp_etypes->size;
  diag "symmetric difference";
  diag join("\n", $got_etypes->symmetric_difference($exp_etypes)->members);
}

done_testing;

