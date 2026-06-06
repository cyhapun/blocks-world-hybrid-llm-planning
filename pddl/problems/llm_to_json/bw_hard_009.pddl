(define (problem bw_hard_009)
  (:domain blocks-world)

  (:objects
    a b c d e f - block
  )

  (:init
    (on_table a)
    (on_table b)
    (on_table c)
    (on_table d)
    (on_table e)
    (on_table f)
    (clear a)
    (clear b)
    (clear c)
    (clear d)
    (clear e)
    (clear f)
    (handempty)
  )

  (:goal
    (and
      (on b c)
      (on a b)
      (on d e)
    )
  )
)
