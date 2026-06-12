(define (problem bw_hard_012)
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
    (clear b)
    (clear c)
    (clear d)
    (on e f)
    (on d e)
    (on b a)
    (handempty)
  )

  (:goal
    (and
      (on c d)
      (on b e)
    )
  )
)
